"""
Tampermonkey에서 내보낸 JSON 파일을 DB로 가져오기
"""

import json
import sys
import os
from datetime import datetime
import pandas as pd
from src.database import RealEstateDB


def parse_floor_number(floor_str):
    """층수 텍스트를 숫자로 변환"""
    if not floor_str or floor_str == '-':
        return 0
    
    import re
    match = re.search(r'(\d+)', floor_str)
    if match:
        return int(match.group(1))
    return 0


def import_json_file(json_file_path, db_path="data/real_estate.db"):
    """
    Tampermonkey에서 내보낸 JSON 파일을 데이터베이스로 가져오기
    
    Args:
        json_file_path: JSON 파일 경로
        db_path: 데이터베이스 파일 경로
    """
    
    # JSON 파일 읽기
    print(f"📂 JSON 파일 읽는 중: {json_file_path}")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False
    
    # 데이터베이스 연결
    db = RealEstateDB(db_path)
    
    # 메타데이터 추출
    metadata = data.get('metadata', {})
    complex_no = metadata.get('complex_no', 'unknown')
    complex_name = metadata.get('complex_name', 'Unknown')
    address = metadata.get('address', '')
    total_households = metadata.get('total_households', 0)
    
    print(f"\n단지 정보:")
    print(f"  - 단지명: {complex_name}")
    print(f"  - 단지번호: {complex_no}")
    print(f"  - 주소: {address}")
    print(f"  - 세대수: {total_households}")
    
    # 단지 정보 저장
    complex_df = pd.DataFrame([{
        '단지번호': complex_no,
        '단지명': complex_name,
        '주소': address,
        '세대수': total_households,
        '건축년도': 2010,  # 기본값
        '면적': 0,  # 기본값
    }])
    db.save_complexes(complex_df)
    print(f"✓ 단지 정보 저장 완료")
    
    # 매물 데이터 변환
    listings = data.get('listings', [])
    
    if not listings:
        print("⚠ 매물 데이터가 없습니다.")
        return False
    
    sale_listings = []
    lease_listings = []
    
    # Tampermonkey 스크립트는 면적별 요약 데이터를 제공
    for listing in listings:
        area_type = listing.get('area_type', '')
        exclusive_area = listing.get('exclusive_area', 0)
        
        # 59m² 또는 84m²만 (±3m²)
        if not (56 <= exclusive_area <= 62 or 81 <= exclusive_area <= 87):
            continue
        
        # 매매 데이터 (sale_price가 있는 경우)
        sale_price = listing.get('sale_price', 0)
        sale_floor = listing.get('sale_floor', '')
        sale_count = listing.get('sale_count', 0)
        
        if sale_price > 0 and sale_count > 0:
            # 층수 파싱
            floor_num = 0
            if sale_floor:
                if '고' in sale_floor:
                    floor_num = 15
                elif '중' in sale_floor:
                    floor_num = 9
                elif sale_floor.isdigit():
                    floor_num = int(sale_floor)
                else:
                    floor_num = 5
            
            # 4층 이상만
            if floor_num >= 4 or floor_num == 0:
                # area_type에서 면적 코드 추출 (예: "86B/59m²" -> "59A")
                import re
                area_match = re.search(r'(\d+)m', area_type)
                if area_match:
                    area_val = int(area_match.group(1))
                    simple_type = "59A" if area_val < 70 else "84A"
                else:
                    simple_type = area_type.split('/')[0] if '/' in area_type else area_type
                
                sale_listings.append({
                    '면적타입': simple_type,
                    '전용면적': exclusive_area,
                    '거래유형': 'SALE',
                    '층': sale_floor,
                    '층수': floor_num,
                    '방향': '',
                    '가격': sale_price * 10000,  # 만원 -> 원
                    '보증금': 0,
                })
        
        # 전세 데이터 (lease_price가 있는 경우)
        lease_price = listing.get('lease_price', 0)
        lease_floor = listing.get('lease_floor', '')
        lease_count = listing.get('lease_count', 0)
        if isinstance(lease_count, str):
            lease_count = int(lease_count) if lease_count.isdigit() else 0
        
        if lease_price > 0 and lease_count > 0:
            # 층수 파싱
            floor_num = 0
            if lease_floor:
                if '고' in lease_floor:
                    floor_num = 15
                elif '중' in lease_floor:
                    floor_num = 9
                elif lease_floor.isdigit():
                    floor_num = int(lease_floor)
                else:
                    floor_num = 5
            
            # 4층 이상만
            if floor_num >= 4 or floor_num == 0:
                # area_type에서 면적 코드 추출
                import re
                area_match = re.search(r'(\d+)m', area_type)
                if area_match:
                    area_val = int(area_match.group(1))
                    simple_type = "59A" if area_val < 70 else "84A"
                else:
                    simple_type = area_type.split('/')[0] if '/' in area_type else area_type
                
                lease_listings.append({
                    '면적타입': simple_type,
                    '전용면적': exclusive_area,
                    '거래유형': 'LEASE',
                    '층': lease_floor,
                    '층수': floor_num,
                    '방향': '',
                    '가격': 0,
                    '보증금': lease_price * 10000,  # 만원 -> 원
                })
    
    # 매매 데이터 저장
    if sale_listings:
        sale_df = pd.DataFrame(sale_listings)
        db.save_prices(sale_df, complex_no)
        print(f"✓ 매매 {len(sale_listings)}개 저장 완료")
    else:
        print("  - 매매 데이터 없음")
    
    # 전세 데이터 저장
    if lease_listings:
        lease_df = pd.DataFrame(lease_listings)
        db.save_prices(lease_df, complex_no)
        print(f"✓ 전세 {len(lease_listings)}개 저장 완료")
    else:
        print("  - 전세 데이터 없음")
    
    print(f"\n🎉 {complex_name} 데이터 가져오기 완료!")
    print(f"   총 {len(sale_listings) + len(lease_listings)}개 매물")
    
    return True


def import_directory(directory_path, db_path="data/real_estate.db"):
    """
    디렉토리 내 모든 JSON 파일 가져오기
    """
    import glob
    
    json_files = glob.glob(os.path.join(directory_path, "naver_*.json"))
    
    if not json_files:
        print(f"⚠ {directory_path}에서 JSON 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 {len(json_files)}개의 JSON 파일 발견\n")
    
    success_count = 0
    for json_file in json_files:
        print(f"\n{'='*60}")
        if import_json_file(json_file, db_path):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"✓ 완료: {success_count}/{len(json_files)}개 파일 가져오기 성공")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python import_json.py <JSON파일경로>")
        print("  python import_json.py <디렉토리경로>  # 디렉토리 내 모든 JSON 가져오기")
        print("\n예시:")
        print("  python import_json.py data/naver_래미안대치팰리스_1234567890.json")
        print("  python import_json.py data/exports/")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isdir(path):
        import_directory(path)
    elif os.path.isfile(path):
        import_json_file(path)
    else:
        print(f"❌ 경로를 찾을 수 없습니다: {path}")
        sys.exit(1)
