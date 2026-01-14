"""
네이버 부동산 크롤러
API 호출 및 데이터 수집
"""

import requests
import pandas as pd
import time
import random
import re
from datetime import datetime
from src.filter import filter_listings


# API 기본 설정
BASE_URL = "https://new.land.naver.com/api"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://new.land.naver.com/',
}

# 필터링 기준
MIN_FLOOR = 4  # 4층 이상만
TARGET_AREAS = [
    (59, 3),  # 59m² ±3m²
    (84, 3),  # 84m² ±3m²
]


def parse_floor_number(floor_str):
    """
    층수 문자열을 숫자로 변환
    예: "5층" -> 5, "저층(1~5층)" -> 3
    """
    if not floor_str:
        return 0
    
    match = re.search(r'(\d+)층', floor_str)
    if match:
        return int(match.group(1))
    
    if '저층' in floor_str or '1~5' in floor_str:
        return 3
    elif '중층' in floor_str or '6~12' in floor_str:
        return 9
    elif '고층' in floor_str or '13층' in floor_str:
        return 15
    
    return 0


def is_target_area(area, target_areas=TARGET_AREAS):
    """주어진 면적이 타겟 범위에 속하는지 확인"""
    for target, tolerance in target_areas:
        if target - tolerance <= area <= target + tolerance:
            return True
    return False


def _generate_sample_complexes(city_code='1168000000', min_households=300) -> pd.DataFrame:
    """API 실패 시 샘플 데이터 생성"""
    print("  └ API 호출 실패. 샘플 데이터로 테스트합니다...")
    
    complexes = [
        {'단지번호': '100001', '단지명': '래미안대치팰리스', '주소': '서울 강남구 대치동', '세대수': 860, '건축년도': 2015, '면적': 123.5},
        {'단지번호': '100002', '단지명': '아크로리버파크', '주소': '서울 강남구 압구정동', '세대수': 1085, '건축년도': 2018, '면적': 142.3},
        {'단지번호': '100003', '단지명': '대치아이파크', '주소': '서울 강남구 대치동', '세대수': 520, '건축년도': 2012, '면적': 98.7},
        {'단지번호': '100004', '단지명': '은마아파트', '주소': '서울 강남구 삼성동', '세대수': 2856, '건축년도': 2008, '면적': 115.2},
        {'단지번호': '100005', '단지명': '개포주공1단지', '주소': '서울 강남구 개포동', '세대수': 1440, '건축년도': 2005, '면적': 102.1},
    ]
    
    return pd.DataFrame(complexes)


def _generate_sample_listings(complex_no: str, transaction_type='SALE') -> pd.DataFrame:
    """
    API 실패 시 샘플 매물 데이터 생성 (필터링 적용)
    Tampermonkey 스크립트의 로직 적용: 층별 가격 차등, 현실적인 전세가율
    """
    
    # 59m², 84m² 타입만 생성
    area_configs = [
        ('59A', 59.8, 18.1),  # 타입, m², 평수
        ('84A', 84.3, 25.5),
    ]
    
    # 4층 이상만 (저층/1-3층 제외 - Tampermonkey 로직)
    floors_options = [
        ('5층', 5),
        ('7층', 7),
        ('9층', 9),
        ('10층', 10),
        ('12층', 12),
        ('중층(6~12층)', 9),
        ('고층(13층 이상)', 15),
    ]
    
    directions = ['남향', '남동향', '남서향', '동향']
    specs = ['정상입주', '확장올수리', '정상입주', '올수리', '세입자끼고', '전세안고']  # 필터링 테스트용
    
    # 단지별 기본 시세 설정 (만원 단위) - 현실적인 강남구 시세
    base_prices = {
        '100001': {'59': 120000, '84': 170000},  # 래미안대치팰리스 - 고급
        '100002': {'59': 130000, '84': 180000},  # 아크로리버파크 - 최고급
        '100003': {'59': 115000, '84': 160000},  # 대치아이파크
        '100004': {'59': 100000, '84': 140000},  # 은마아파트 - 구축
        '100005': {'59': 95000, '84': 135000},   # 개포주공1단지 - 재건축 예정
    }
    
    base_price_59 = base_prices.get(complex_no, {'59': 110000, '84': 155000})['59']
    base_price_84 = base_prices.get(complex_no, {'59': 110000, '84': 155000})['84']
    
    listings = []
    
    # 각 면적 타입별로 3-6개씩 생성
    for area_type, area, pyeong in area_configs:
        num_listings = random.randint(3, 6)
        
        # 이 면적 타입의 기본 가격
        base_price = base_price_59 if area < 70 else base_price_84
        
        for i in range(num_listings):
            floor_text, floor_num = random.choice(floors_options)
            
            # 층수에 따른 가격 조정 (Tampermonkey 로직 반영)
            # 중층(6-12층)이 가장 비싸고, 저층은 저렴, 고층도 약간 저렴
            floor_multiplier = 1.0
            if floor_num <= 5:
                floor_multiplier = 0.95  # 5층은 약간 저렴
            elif 6 <= floor_num <= 12:
                floor_multiplier = 1.02  # 중층이 가장 비쌈
            elif floor_num >= 13:
                floor_multiplier = 0.98  # 고층은 약간 저렴 (엘리베이터 혼잡)
            
            # 매물 간 가격 변동 (±5%)
            price_variation = random.uniform(0.95, 1.05)
            
            listing = {
                '면적타입': area_type,
                '전용면적': area,
                '거래유형': transaction_type,
                '층': floor_text,
                '층수': floor_num,
                '방향': random.choice(directions),
                'spec': random.choice(specs),  # 세안고 필터링용
            }
            
            if transaction_type == 'SALE':
                # 매매가 계산
                sale_price = int(base_price * floor_multiplier * price_variation)
                listing['가격'] = sale_price * 10000  # 원 단위로 변환
                listing['보증금'] = 0
                
            else:  # LEASE
                # 전세가 = 매매가의 70-85% (현실적인 전세가율)
                # Tampermonkey 스크립트 분석 결과 전세가율이 70-85% 정도
                lease_ratio = random.uniform(0.70, 0.85)
                sale_price = int(base_price * floor_multiplier * price_variation)
                lease_price = int(sale_price * lease_ratio)
                
                listing['가격'] = 0
                listing['보증금'] = lease_price * 10000  # 원 단위로 변환
            
            listings.append(listing)
    
    # 필터링 적용
    df = pd.DataFrame(listings)
    filter_options = {
        'exclude_seango': True,
        'exclude_low_floors': True,
        'include_large_area': False,
    }
    filtered_df = filter_listings(df, filter_options)
    
    return filtered_df


def get_filtered_complexes(city_code='1168000000', min_households=300, use_sample=True) -> pd.DataFrame:
    """
    네이버 부동산 API를 통해 특정 지역의 아파트 단지 리스트 조회
    
    Args:
        city_code: 지역코드 (기본값: 1168000000 강남구)
        min_households: 최소 세대수
        use_sample: True면 샘플 데이터 사용
    
    Returns:
        DataFrame with columns: 단지번호, 단지명, 주소, 세대수, 면적
    """
    if use_sample:
        return _generate_sample_complexes(city_code, min_households)
    
    url = f"{BASE_URL}/complexes"
    params = {
        'cortarNo': city_code,
        'realEstateType': 'APT',
        'order': 'householdCountDesc'
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        complexes = []
        
        for item in data.get('complexList', []):
            if item.get('totalHouseholdCount', 0) >= min_households:
                complexes.append({
                    '단지번호': item.get('complexNo'),
                    '단지명': item.get('complexName'),
                    '주소': item.get('cortarAddress'),
                    '세대수': item.get('totalHouseholdCount'),
                    '면적': item.get('pyeongArea', 0)
                })
        
        return pd.DataFrame(complexes)
    
    except Exception as e:
        print(f"⚠ API 요청 실패: {e}")
        return _generate_sample_complexes(city_code, min_households)


def get_listings_api(complex_no: str, transaction_type='SALE', use_sample=True) -> pd.DataFrame:
    """
    특정 단지의 매물 리스트 조회
    
    Args:
        complex_no: 단지번호
        transaction_type: 'SALE' (매매) 또는 'LEASE' (전세)
        use_sample: True면 샘플 데이터 사용
    
    Returns:
        DataFrame with columns: 면적타입, 전용면적, 거래유형, 층, 층수, 방향, 가격, 보증금
    """
    if use_sample:
        return _generate_sample_listings(complex_no, transaction_type)
    
    # 실제 API 호출 (현재 429 에러로 사용 불가)
    trade_type_code = 'A1' if transaction_type == 'SALE' else 'B1'
    url = f"{BASE_URL}/articles/complex/{complex_no}"
    params = {
        'realEstateType': 'APT',
        'tradeType': trade_type_code,
        'priceType': 'RETAIL',
        'page': 1,
        'complexNo': complex_no,
        'type': 'list',
        'order': 'rank'
    }
    
    try:
        time.sleep(random.uniform(2.0, 4.0))  # Rate limiting
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        articles = data.get('articleList', [])
        
        listings = []
        for article in articles:
            area = float(article.get('area', 0))
            
            # 필터링: 59m² 또는 84m²
            if not is_target_area(area):
                continue
            
            floor_info = article.get('floorInfo', '')
            floor_num = parse_floor_number(floor_info)
            
            # 필터링: 4층 이상
            if floor_num < MIN_FLOOR:
                continue
            
            area_type = "59A" if area < 70 else "84A"
            price = int(article.get('dealOrWarrantPrc', 0))
            
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
            
            listings.append(listing)
        
        return pd.DataFrame(listings)
    
    except Exception as e:
        print(f"  API 호출 실패, 샘플 데이터로 대체")
        return _generate_sample_listings(complex_no, transaction_type)
