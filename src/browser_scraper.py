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
        매물 데이터 추출 (강건한 선택자 사용)
        
        특징:
        - 여러 선택자 경로 시도 (폴백)
        - 광고 매물 필터링
        - 동적 콘텐츠 처리
        - 상세한 에러 로깅
        
        Returns:
            DataFrame with columns: 면적타입, 전용면적, 거래유형, 층, 층수, 방향, 가격, 보증금, spec
        """
        try:
            # JavaScript로 DOM에서 데이터 추출 (강건한 선택자)
            listings_data = await self.page.evaluate('''
                () => {
                    const listings = [];
                    const articles = document.querySelectorAll('#articleListArea .article-item, #articleListArea > div');
                    
                    if (articles.length === 0) {
                        console.warn('매물 엘리먼트를 찾을 수 없음');
                        return listings;
                    }
                    
                    articles.forEach((article, idx) => {
                        try {
                            // 광고 매물 필터링
                            if (article.classList.contains('ad') || article.classList.contains('sponsored')) {
                                return;
                            }
                            
                            // 1단계: 면적 및 층수 정보 추출 (여러 경로 시도)
                            let specText = null;
                            let aptInfo = [];
                            
                            // 경로 1: .info_area .line .spec
                            specText = article.querySelector('.info_area .line .spec');
                            if (specText) {
                                aptInfo = specText.innerText.split(',').map(s => s.trim());
                            }
                            
                            // 경로 2: .info_area 내 텍스트 파싱
                            if (aptInfo.length < 2) {
                                const infoArea = article.querySelector('.info_area');
                                if (infoArea) {
                                    const infoText = infoArea.innerText;
                                    aptInfo = infoText.split('\\n').slice(0, 3).map(s => s.trim()).filter(s => s);
                                }
                            }
                            
                            // 경로 3: 전체 텍스트에서 정규식으로 추출
                            if (aptInfo.length < 2) {
                                const fullText = article.innerText;
                                const areaMatch = fullText.match(/(\\d+\\.?\\d*)m²/);
                                const floorMatch = fullText.match(/(\\d+)\\/\\d+층|((저|중|고)층)/);
                                
                                if (areaMatch) {
                                    aptInfo = [areaMatch[0], floorMatch ? floorMatch[0] : '정보없음'];
                                }
                            }
                            
                            if (aptInfo.length < 2) {
                                console.warn('면적/층수 정보 없음 - 스킵');
                                return;
                            }
                            
                            const areaText = aptInfo[0];      // "84m²"
                            const floorText = aptInfo[1];     // "5/10층"
                            
                            // 2단계: 전용면적 추출
                            const areaMatch = areaText.match(/(\\d+\\.?\\d*)/);
                            if (!areaMatch) {
                                console.warn('면적 파싱 실패:', areaText);
                                return;
                            }
                            const exclusiveArea = parseFloat(areaMatch[1]);
                            
                            // 3단계: 거래 유형 및 가격 추출
                            const priceLines = article.querySelectorAll('.price-line, .price_line, .price, [class*="price"]');
                            let tradeType = '';
                            let priceText = '';
                            
                            // 거래유형 찾기
                            const tradeElem = article.querySelector('[class*="trade"], [class*="type"]');
                            if (tradeElem) {
                                tradeType = tradeElem.innerText.trim();
                            }
                            
                            // 가격 텍스트 찾기
                            let foundPrice = false;
                            for (let priceElem of priceLines) {
                                const text = priceElem.innerText?.trim() || '';
                                if (text.match(/\\d+/) && (text.includes('억') || text.includes('만') || text.match(/^\\d+$/))) {
                                    priceText = text;
                                    foundPrice = true;
                                    break;
                                }
                            }
                            
                            // 가격 못 찾으면 전체 텍스트에서 찾기
                            if (!foundPrice) {
                                const fullText = article.innerText;
                                const priceMatch = fullText.match(/(\\d+억\\s*\\d*만|\\d+만|\\d+억)/);
                                if (priceMatch) {
                                    priceText = priceMatch[1];
                                }
                            }
                            
                            // 4단계: 가격 파싱 (억/만원 → 만원)
                            let price = 0;
                            if (priceText) {
                                if (priceText.includes('억')) {
                                    const parts = priceText.replace(/,/g, '').split('억');
                                    const eok = parseInt(parts[0]) || 0;
                                    const man = parts[1] ? parseInt(parts[1].replace(/[^0-9]/g, '')) : 0;
                                    price = eok * 10000 + man;
                                } else {
                                    price = parseInt(priceText.replace(/[^0-9]/g, '')) || 0;
                                }
                            }
                            
                            // 5단계: 특이사항 추출
                            let spec = '';
                            const specElems = article.querySelectorAll('[class*="spec"], [class*="note"], .etc');
                            for (let elem of specElems) {
                                const text = elem.innerText?.trim();
                                if (text && text.length > 0 && text.length < 100) {
                                    spec = text;
                                    break;
                                }
                            }
                            
                            // 6단계: 방향 추출
                            const dirMatch = article.innerText.match(/([동서남북]+향|정남향|남동향|남서향)/);
                            const direction = dirMatch ? dirMatch[1] : '';
                            
                            listings.push({
                                area_text: areaText,
                                exclusive_area: exclusiveArea,
                                trade_type: tradeType || '정보없음',
                                floor: floorText,
                                price_text: priceText,
                                price: price,
                                spec: spec,
                                direction: direction
                            });
                            
                        } catch (e) {
                            console.error(`[${idx}] 매물 파싱 오류:`, e.message);
                        }
                    });
                    
                    console.log(`총 ${listings.length}개 매물 추출 완료`);
                    return listings;
                }
            ''')
            
            # DataFrame 변환
            if not listings_data:
                print("⚠ 추출된 매물 없음 - JavaScript 평가 실패 또는 매물 없음")
                return pd.DataFrame()
            
            # Python DataFrame으로 변환
            df_list = []
            skipped = 0
            
            for idx, item in enumerate(listings_data):
                try:
                    # 데이터 검증
                    if not item.get('exclusive_area'):
                        skipped += 1
                        continue
                    
                    # 층수 추출
                    floor_match = re.search(r'(\d+)', item.get('floor', ''))
                    floor_num = int(floor_match.group(1)) if floor_match else 0
                    
                    # 면적 타입 결정 (59A, 84A 등)
                    area = item['exclusive_area']
                    if 56 <= area <= 62:
                        area_type = '59A'
                    elif 72 <= area <= 78:
                        area_type = '75A'
                    elif 81 <= area <= 87:
                        area_type = '84A'
                    else:
                        area_type = f"{int(area)}A"
                    
                    # 거래 유형 변환
                    trade_type_map = {
                        '매매': 'SALE',
                        '전세': 'LEASE',
                        '월세': 'RENT',
                        '정보없음': 'SALE'  # 기본값
                    }
                    trade_type = trade_type_map.get(item.get('trade_type', ''), 'SALE')
                    
                    listing = {
                        '면적타입': area_type,
                        '전용면적': area,
                        '거래유형': trade_type,
                        '층': item.get('floor', '정보없음'),
                        '층수': floor_num,
                        '방향': item.get('direction', ''),
                        '가격': item.get('price', 0) if trade_type == 'SALE' else 0,
                        '보증금': item.get('price', 0) if trade_type == 'LEASE' else 0,
                        'spec': item.get('spec', '')
                    }
                    
                    df_list.append(listing)
                    
                except Exception as e:
                    print(f"  ⚠ [{idx}] 매물 처리 오류: {e}")
                    skipped += 1
                    continue
            
            df = pd.DataFrame(df_list)
            print(f"✓ 매물 {len(df)}개 추출 완료" + (f" (스킵: {skipped}개)" if skipped > 0 else ""))
            
            return df
            
        except Exception as e:
            print(f"❌ 매물 추출 실패: {e}")
            import traceback
            traceback.print_exc()
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


async def scrape_complex(complex_no: str, headless: bool = True) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
    """
    특정 단지의 브라우저 자동화 데이터 수집
    main.py에서 호출하는 래퍼 함수
    
    Args:
        complex_no: 단지 번호
        headless: 헤드리스 모드 여부
    
    Returns:
        (complex_info, sale_df, lease_df)
    """
    scraper = NaverRealEstateScraper(headless=headless)
    
    try:
        await scraper.start()
        
        # 단지 페이지 이동
        if not await scraper.navigate_to_complex(complex_no):
            print(f"❌ 단지 페이지 로드 실패: {complex_no}")
            return {}, pd.DataFrame(), pd.DataFrame()
        
        # 매물 리스트 스크롤
        await scraper.scroll_article_list(max_scrolls=10)
        
        # 단지 정보 추출
        complex_info = await scraper.get_complex_info()
        
        # 매물 데이터 추출
        listings_df = await scraper.extract_listings()
        
        if listings_df.empty:
            print(f"⚠ {complex_no}에서 추출된 매물 없음")
            return complex_info, pd.DataFrame(), pd.DataFrame()
        
        # 매매/전세 분리
        sale_df = listings_df[listings_df['거래유형'] == 'SALE'].copy()
        lease_df = listings_df[listings_df['거래유형'] == 'LEASE'].copy()
        
        print(f"✓ {complex_no} 데이터 수집 완료: 매매 {len(sale_df)}개, 전세 {len(lease_df)}개")
        
        return complex_info, sale_df, lease_df
        
    except Exception as e:
        print(f"❌ 스크래핑 중 오류: {e}")
        return {}, pd.DataFrame(), pd.DataFrame()
    
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_scraping())
