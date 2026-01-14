"""
네이버 부동산 브라우저 자동화 스크래퍼 (Playwright)
Tampermonkey 스크립트 로직을 Python으로 재구현
"""

import asyncio
import time
import re
from typing import List, Dict, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser
import pandas as pd


# 네이버 부동산 기본 URL
NAVER_REAL_ESTATE_URL = "https://new.land.naver.com"


class NaverRealEstateScraper:
    """네이버 부동산 브라우저 자동화 스크래퍼"""
    
    def __init__(self, headless: bool = False):
        """
        Args:
            headless: True면 브라우저 UI 없이 실행
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        
        # User Agent 설정
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        print("✓ 브라우저 시작됨")
    
    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("✓ 브라우저 종료됨")
    
    async def navigate_to_complex(self, complex_no: str) -> bool:
        """
        특정 단지 페이지로 이동
        
        Args:
            complex_no: 단지 번호 (예: "180280")
        
        Returns:
            성공 여부
        """
        url = f"{NAVER_REAL_ESTATE_URL}/complexes/{complex_no}"
        
        try:
            print(f"📍 페이지 이동 중: {url}")
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 페이지 로드 대기
            await self.page.wait_for_selector('#complexTitle', timeout=10000)
            
            # 단지명 확인
            complex_name = await self.page.locator('#complexTitle').inner_text()
            print(f"✓ 단지 로드 완료: {complex_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 페이지 로드 실패: {e}")
            return False
    
    async def scroll_article_list(self, max_scrolls: int = 10):
        """
        매물 리스트 스크롤하여 모든 데이터 로드
        
        Args:
            max_scrolls: 최대 스크롤 횟수
        """
        try:
            # 매물 리스트 영역 찾기
            article_list_selector = '#articleListArea'
            await self.page.wait_for_selector(article_list_selector, timeout=10000)
            
            print("📜 매물 리스트 스크롤 중...")
            
            for i in range(max_scrolls):
                # 스크롤 실행
                await self.page.evaluate('''
                    () => {
                        const listArea = document.querySelector('#articleListArea');
                        if (listArea) {
                            listArea.scrollTop = listArea.scrollHeight;
                        }
                    }
                ''')
                
                await asyncio.sleep(1)  # 데이터 로드 대기
            
            print(f"✓ 스크롤 완료 ({max_scrolls}회)")
            
        except Exception as e:
            print(f"⚠ 스크롤 중 오류: {e}")
    
    async def extract_listings(self) -> pd.DataFrame:
        """
        매물 데이터 추출 (Tampermonkey 로직 재현)
        
        Returns:
            DataFrame with columns: 면적타입, 전용면적, 거래유형, 층, 층수, 방향, 가격, 보증금, spec
        """
        try:
            # JavaScript로 DOM에서 데이터 추출
            listings_data = await self.page.evaluate('''
                () => {
                    const listings = [];
                    const articles = document.querySelectorAll('#articleListArea > div');
                    
                    articles.forEach(article => {
                        try {
                            // 면적 및 층수 정보
                            const specText = article.querySelector('.info_area .line .spec');
                            if (!specText) return;
                            
                            const aptInfo = specText.innerText.split(', ');
                            if (aptInfo.length < 2) return;
                            
                            const areaText = aptInfo[0];  // "103/84m²"
                            const floorText = aptInfo[1]; // "5/10층"
                            
                            // 전용면적 추출
                            const areaMatch = areaText.match(/(\\d+)m/);
                            if (!areaMatch) return;
                            const exclusiveArea = parseFloat(areaMatch[1]);
                            
                            // 거래 유형 및 가격
                            const tradeTypeElem = article.querySelector('.price_line .type');
                            const priceElem = article.querySelector('.price_line .price');
                            
                            if (!tradeTypeElem || !priceElem) return;
                            
                            const tradeType = tradeTypeElem.innerText.trim();
                            const priceText = priceElem.innerText.trim();
                            
                            // 가격 파싱 (억/만원 → 만원)
                            let price = 0;
                            if (priceText.includes('억')) {
                                const parts = priceText.replace(/,/g, '').split('억');
                                const eok = parseInt(parts[0]) || 0;
                                const man = parts[1] ? parseInt(parts[1].replace(/[^0-9]/g, '')) : 0;
                                price = eok * 10000 + man;
                            } else {
                                price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
                            }
                            
                            // 특이사항 (세안고, 올수리 등)
                            const specElem = article.querySelector('.info_area > p:nth-child(2) > span');
                            const spec = specElem ? specElem.innerText.trim() : '';
                            
                            // 방향 (없을 수 있음)
                            const direction = '';
                            
                            listings.push({
                                area_text: areaText,
                                exclusive_area: exclusiveArea,
                                trade_type: tradeType,
                                floor: floorText,
                                price_text: priceText,
                                price: price,
                                spec: spec,
                                direction: direction
                            });
                            
                        } catch (e) {
                            console.error('매물 파싱 오류:', e);
                        }
                    });
                    
                    return listings;
                }
            ''')
            
            # DataFrame 변환
            if not listings_data:
                print("⚠ 추출된 매물 없음")
                return pd.DataFrame()
            
            # Python DataFrame으로 변환
            df_list = []
            for item in listings_data:
                # 층수 추출
                floor_match = re.search(r'(\d+)/', item['floor'])
                floor_num = int(floor_match.group(1)) if floor_match else 0
                
                # 면적 타입 결정 (59A, 84A)
                area = item['exclusive_area']
                if 56 <= area <= 62:
                    area_type = '59A'
                elif 81 <= area <= 87:
                    area_type = '84A'
                else:
                    area_type = f"{int(area)}A"
                
                # 거래 유형 변환
                trade_type_map = {
                    '매매': 'SALE',
                    '전세': 'LEASE',
                    '월세': 'RENT'
                }
                trade_type = trade_type_map.get(item['trade_type'], 'SALE')
                
                listing = {
                    '면적타입': area_type,
                    '전용면적': area,
                    '거래유형': trade_type,
                    '층': item['floor'],
                    '층수': floor_num,
                    '방향': item['direction'],
                    '가격': item['price'] if trade_type == 'SALE' else 0,
                    '보증금': item['price'] if trade_type == 'LEASE' else 0,
                    'spec': item['spec']
                }
                
                df_list.append(listing)
            
            df = pd.DataFrame(df_list)
            print(f"✓ 매물 {len(df)}개 추출 완료")
            
            return df
            
        except Exception as e:
            print(f"❌ 매물 추출 실패: {e}")
            return pd.DataFrame()
    
    async def get_complex_info(self) -> Dict:
        """단지 기본 정보 추출"""
        try:
            complex_name = await self.page.locator('#complexTitle').inner_text()
            
            # 주소 추출 (있는 경우)
            address = ""
            try:
                address_elem = await self.page.locator('#summaryInfo .complex_address').first
                address = await address_elem.inner_text()
            except:
                pass
            
            # URL에서 단지 번호 추출
            current_url = self.page.url
            match = re.search(r'/complexes/(\d+)', current_url)
            complex_no = match.group(1) if match else 'unknown'
            
            return {
                '단지번호': complex_no,
                '단지명': complex_name,
                '주소': address,
                '세대수': 0,  # API 호출 필요
                '건축년도': 2010,  # 기본값
                '면적': 0,
            }
            
        except Exception as e:
            print(f"❌ 단지 정보 추출 실패: {e}")
            return {}


async def scrape_complex(complex_no: str, headless: bool = False) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    """
    단지 전체 데이터 수집 (정보 + 매매 + 전세)
    
    Args:
        complex_no: 단지 번호
        headless: 브라우저 headless 모드
    
    Returns:
        (complex_info, sale_df, lease_df)
    """
    scraper = NaverRealEstateScraper(headless=headless)
    
    try:
        await scraper.start()
        
        # 단지 페이지 이동
        success = await scraper.navigate_to_complex(complex_no)
        if not success:
            return {}, pd.DataFrame(), pd.DataFrame()
        
        # 스크롤하여 모든 매물 로드
        await scraper.scroll_article_list(max_scrolls=10)
        
        # 단지 정보 추출
        complex_info = await scraper.get_complex_info()
        
        # 매물 데이터 추출
        all_listings = await scraper.extract_listings()
        
        # 매매/전세 분리
        sale_df = all_listings[all_listings['거래유형'] == 'SALE'].copy() if not all_listings.empty else pd.DataFrame()
        lease_df = all_listings[all_listings['거래유형'] == 'LEASE'].copy() if not all_listings.empty else pd.DataFrame()
        
        print(f"\n✓ 수집 완료: 매매 {len(sale_df)}개, 전세 {len(lease_df)}개")
        
        return complex_info, sale_df, lease_df
        
    finally:
        await scraper.close()


# 테스트 함수
async def test_scraping():
    """브라우저 스크래핑 테스트"""
    # 테스트 단지: 은마아파트 (180280)
    test_complex = '180280'
    
    print("=== 브라우저 스크래핑 테스트 ===\n")
    print(f"테스트 단지: {test_complex}\n")
    
    info, sale, lease = await scrape_complex(test_complex, headless=False)
    
    print("\n" + "="*60)
    print("📊 수집 결과")
    print("="*60)
    print(f"\n단지 정보:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    if not sale.empty:
        print(f"\n매매 매물 ({len(sale)}개):")
        print(sale[['면적타입', '전용면적', '층수', '가격', 'spec']].head(5))
    
    if not lease.empty:
        print(f"\n전세 매물 ({len(lease)}개):")
        print(lease[['면적타입', '전용면적', '층수', '보증금', 'spec']].head(5))


if __name__ == "__main__":
    asyncio.run(test_scraping())
