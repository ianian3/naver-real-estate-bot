from src.crawler import get_filtered_complexes, get_listings_api
from src.database import RealEstateDB
from src.browser_scraper import scrape_complex
import time
import asyncio

# === 설정 ===
USE_BROWSER_SCRAPING = True   # ✅ 브라우저 자동화 활성화 (실제 네이버 데이터 수집)
HEADLESS = False              # ✅ 브라우저 창 보이도록 설정

def job():
    # 1. DB 연결
    db = RealEstateDB()

    # 2. 단지 리스트 갱신 (필요 시)
    print(">>> 단지 리스트 갱신 중...")
    complexes = get_filtered_complexes() 
    db.save_complexes(complexes)

    # 3. 가격 데이터 수집 (매매 + 전세)
    print(">>> 가격 데이터 수집 시작...")
    print("  필터링 기준: 4층 이상, 59m²/84m² 면적")
    
    for idx, row in complexes.iterrows():
        c_no = row['단지번호']
        c_name = row['단지명']
        
        print(f"\n[{idx+1}/{len(complexes)}] {c_name} ({c_no})")
        
        if USE_BROWSER_SCRAPING:
            # 브라우저 자동화 사용
            print("  - 브라우저 자동화로 데이터 수집 중...")
            try:
                complex_info, df_sale, df_lease = asyncio.run(
                    scrape_complex(c_no, headless=HEADLESS)
                )
                
                # 필터링 적용
                from src.filter import filter_listings
                if not df_sale.empty:
                    df_sale = filter_listings(df_sale)
                    db.save_prices(df_sale, c_no)
                if not df_lease.empty:
                    df_lease = filter_listings(df_lease)
                    db.save_prices(df_lease, c_no)
                
                time.sleep(3)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ 브라우저 스크래핑 실패: {e}")
                continue
        else:
            # 기존 API/샘플 데이터 방식
            print("  - 매매 데이터 조회 중...")
            df_sale = get_listings_api(c_no, transaction_type='SALE')
            if not df_sale.empty:
                from src.filter import filter_listings
                df_sale = filter_listings(df_sale)
                db.save_prices(df_sale, c_no)
            time.sleep(1)
            
            print("  - 전세 데이터 조회 중...")
            df_lease = get_listings_api(c_no, transaction_type='LEASE')
            if not df_lease.empty:
                from src.filter import filter_listings
                df_lease = filter_listings(df_lease)
                db.save_prices(df_lease, c_no)
            time.sleep(1)

    print("\n>>> 수집 완료")
    
    # 결과 요약
    print("\n=== 수집 결과 요약 ===")
    db.cursor.execute("SELECT COUNT(*) FROM complexes")
    complex_count = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM prices WHERE transaction_type='SALE'")
    sale_count = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(*) FROM prices WHERE transaction_type='LEASE'")
    lease_count = db.cursor.fetchone()[0]
    
    db.cursor.execute("SELECT COUNT(DISTINCT area_type) FROM prices")
    area_types = db.cursor.fetchone()[0]
    
    print(f"단지 수: {complex_count}개")
    print(f"매매 매물: {sale_count}개")
    print(f"전세 매물: {lease_count}개")
    print(f"면적 타입: {area_types}개")

if __name__ == "__main__":
    job()