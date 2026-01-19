"""
네이버 부동산 API 직접 호출 스크래퍼
Network 분석을 통해 발견한 내부 API 사용
"""

import requests
import time
import re
from typing import List, Dict, Optional, Tuple
import pandas as pd
import random


# 네이버 API 기본 설정
BASE_URL = "https://new.land.naver.com/api"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://new.land.naver.com/',
    'Accept': 'application/json',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}


def parse_price_number(price) -> int:
    """가격을 정수로 변환 (단위: 원)"""
    if isinstance(price, (int, float)):
        # 가격이 만원 단위로 저장되어 있을 경우
        return int(price) * 10000 if price < 1000000 else int(price)
    return 0


def parse_floor_number(floor_info: str) -> int:
    """층수 텍스트를 숫자로 변환"""
    if not floor_info:
        return 0
    
    # "5층" 형식
    match = re.search(r'(\d+)', str(floor_info))
    if match:
        return int(match.group(1))
    
    return 0


def scrape_complex_overview(complex_no: str) -> Dict:
    """
    단지 개요 정보 조회
    API: /api/complexes/overview/{complex_no}
    """
    url = f"{BASE_URL}/complexes/overview/{complex_no}"
    params = {'complexNo': complex_no}
    
    try:
        time.sleep(random.uniform(0.5, 1.5))  # Rate limiting
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'complex_no': complex_no,
            'complex_name': data.get('complexName', ''),
            'address': f"{data.get('cortarAddress', '')} {data.get('dealAddress', '')}".strip(),
            'households': data.get('totalHouseholdCount', 0),
            'build_year': int(data.get('useApproveYmd', '2010')[:4]),  # YYYYMMDD 형식
        }
    
    except Exception as e:
        print(f"  ⚠ 단지 정보 조회 실패 ({complex_no}): {e}")
        return {}


def scrape_articles(complex_no: str, trade_type: str = 'A1', max_pages: int = 3) -> List[Dict]:
    """
    매물 리스트 조회
    API: /api/articles/complex/{complex_no}
    
    Args:
        complex_no: 단지번호
        trade_type: A1 (매매), B1 (전세), C1 (월세)
        max_pages: 최대 페이지 수
    
    Returns:
        List of listings
    """
    all_listings = []
    transaction_type = 'SALE' if trade_type == 'A1' else 'LEASE'
    retry_count = 0
    max_retries = 3
    base_wait = 2  # 초
    
    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/articles/complex/{complex_no}"
        params = {
            'realEstateType': 'APT',
            'tradeType': trade_type,
            'priceType': 'RETAIL',
            'page': page,
            'complexNo': complex_no,
            'type': 'list',
            'order': 'rank'
        }
        
        while retry_count < max_retries:
            try:
                wait_time = base_wait * (2 ** retry_count)  # 지수 백오프
                time.sleep(random.uniform(wait_time - 0.5, wait_time + 0.5))  # Rate limiting
                response = requests.get(url, params=params, headers=HEADERS, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                articles = data.get('articleList', [])
                
                if not articles:
                    break  # 더 이상 데이터 없음
                
                for article in articles:
                    # 면적 확인
                    area = float(article.get('area', 0))
                    
                    # 59m² 또는 84m² 필터링 (±3m²)
                    if not (56 <= area <= 62 or 81 <= area <= 87):
                        continue
                    
                    # 층수 확인
                    floor_info = article.get('floorInfo', '')
                    floor_num = parse_floor_number(floor_info)
                    
                    # 4층 이상만
                    if floor_num < 4:
                        continue
                    
                    # 가격
                    price = parse_price_number(article.get('dealOrWarrantPrc', 0))
                    
                    # 면적타입
                    area_type = "59A" if area < 70 else "84A"
                    
                    listing = {
                        '면적타입': area_type,
                        '전용면적': area,
                        '거래유형': transaction_type,
                        '층': floor_info,
                        '층수': floor_num,
                        '방향': article.get('direction', ''),
                        '가격': price if transaction_type == 'SALE' else 0,
                        '보증금': price if transaction_type == 'LEASE' else 0,
                    }
                    
                    all_listings.append(listing)
                
                retry_count = 0  # 성공 시 리트라이 카운트 리셋
                break  # 루프 탈출
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit 에러 - 지수 백오프로 재시도
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"  ⚠ Rate limit 도달 - 최대 재시도 횟수 초과")
                        return all_listings
                    
                    wait_time = base_wait * (2 ** retry_count)
                    print(f"  ⚠ Rate limit (429) - {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                else:
                    print(f"  ⚠ HTTP 오류: {e}")
                    return all_listings
            
            except Exception as e:
                print(f"  ⚠ API 오류: {e}")
                return all_listings
    
    print(f"    - {transaction_type}: {len(all_listings)}개 매물 추출")
    return all_listings


def scrape_complex_full_data(complex_no: str) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    """
    단지의 전체 데이터 수집 (정보 + 매매 + 전세)
    
    Returns:
        (complex_info, sale_df, lease_df)
    """
    print(f"\n[{complex_no}] 데이터 수집 중...")
    
    # 1. 단지 정보
    complex_info = scrape_complex_overview(complex_no)
    if complex_info:
        print(f"  ✓ {complex_info.get('complex_name', 'Unknown')}")
    
    # 2. 매매 매물
    sale_listings = scrape_articles(complex_no, 'A1', max_pages=2)
    sale_df = pd.DataFrame(sale_listings) if sale_listings else pd.DataFrame()
    
    # 3. 전세 매물
    lease_listings = scrape_articles(complex_no, 'B1', max_pages=2)
    lease_df = pd.DataFrame(lease_listings) if lease_listings else pd.DataFrame()
    
    return complex_info, sale_df, lease_df


def get_gangnam_complexes_sample() -> List[str]:
    """
    강남구 주요 아파트 단지 번호 (실제로는 검색 API 필요)
    현재는 알려진 단지 번호 사용
    """
    return [
        '12957',   # 래미안대치팰리스
        '12965',   # 아크로리버파크  
        '180280',  # 은마아파트
        '12661',   # 개포주공1단지
        '11308',   # 대치아이파크
    ]


# 테스트 함수
def test_api_scraping():
    """API 스크래핑 테스트"""
    # 테스트: 래미안대치팰리스
    test_complex = '12957'
    
    info, sale, lease = scrape_complex_full_data(test_complex)
    
    print("\n" + "="*50)
    print("📊 수집 결과")
    print("="*50)
    print(f"\n단지 정보: {info}")
    print(f"\n매매 {len(sale)}개:")
    if not sale.empty:
        print(sale[['면적타입', '전용면적', '층수', '가격']].head(10))
    print(f"\n전세 {len(lease)}개:")
    if not lease.empty:
        print(lease[['면적타입', '전용면적', '층수', '보증금']].head(10))


if __name__ == "__main__":
    test_api_scraping()
