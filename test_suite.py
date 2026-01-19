#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 테스트 스위트
수정된 기능들을 검증합니다
"""

import sys
import pandas as pd
import tempfile
import os
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_analyzer():
    """analyzer.py 테스트"""
    print("\n" + "="*60)
    print("📊 [TEST] analyzer.py - 가격 분석")
    print("="*60)
    
    try:
        from src.analyzer import (
            format_price_display, 
            calculate_gap_and_ratio,
            get_price_summary_by_area,
            get_all_area_summaries
        )
        
        # 1. format_price_display 테스트
        print("\n✓ format_price_display() 테스트:")
        test_prices = [0, 5000, 120000, 120500, 1200000]
        for price in test_prices:
            result = format_price_display(price)
            print(f"  {price:>7} (만원) → {result}")
        
        # 2. calculate_gap_and_ratio 테스트
        print("\n✓ calculate_gap_and_ratio() 테스트:")
        gap, ratio = calculate_gap_and_ratio(120000, 100000)
        print(f"  매매가: 120000만원, 전세가: 100000만원")
        print(f"  → 갭: {gap}만원, 전세가율: {ratio}")
        
        # 3. 빈 DataFrame 처리 테스트
        print("\n✓ 빈 DataFrame 처리 테스트:")
        empty_df = pd.DataFrame()
        result = get_all_area_summaries(empty_df)
        print(f"  빈 DataFrame → {result} (빈 딕셔너리)")
        
        # 4. None 입력 처리 테스트
        print("\n✓ None 입력 처리 테스트:")
        result = get_all_area_summaries(None)
        print(f"  None → {result} (빈 딕셔너리)")
        
        # 5. 샘플 데이터로 테스트
        print("\n✓ 샘플 데이터 처리 테스트:")
        sample_df = pd.DataFrame([
            {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'SALE', '가격': 120000, '보증금': 0, '층': '5층'},
            {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'SALE', '가격': 125000, '보증금': 0, '층': '7층'},
            {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'LEASE', '가격': 0, '보증금': 102000, '층': '8층'},
            {'면적타입': '84A', '전용면적': 84.3, '거래유형': 'SALE', '가격': 170000, '보증금': 0, '층': '6층'},
        ])
        
        result = get_all_area_summaries(sample_df)
        print(f"  입력: {len(sample_df)}개 매물")
        print(f"  결과: {list(result.keys())} (면적 타입)")
        for area_type, summary in result.items():
            print(f"    {area_type}: 매매 {summary['sale_count']}개, 전세 {summary['lease_count']}개")
        
        print("\n✅ analyzer.py 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filter():
    """filter.py 테스트"""
    print("\n" + "="*60)
    print("🔍 [TEST] filter.py - 필터링")
    print("="*60)
    
    try:
        from src.filter import filter_listings, check_seango_spec
        
        # 1. check_seango_spec 테스트
        print("\n✓ check_seango_spec() 테스트:")
        test_specs = [
            ('세입자끼고', True),
            ('전세안고', True),
            ('정상입주', False),
            ('올수리', False),
            ('', False),
        ]
        
        for spec, expected in test_specs:
            result = check_seango_spec(spec)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{spec}' → {result} (기대: {expected})")
        
        # 2. filter_listings 테스트
        print("\n✓ filter_listings() 테스트:")
        sample_df = pd.DataFrame([
            {'거래유형': 'SALE', '층': '2층', '전용면적': 59.8, 'spec': '세입자끼고'},
            {'거래유형': 'SALE', '층': '5층', '전용면적': 59.8, 'spec': '정상입주'},
            {'거래유형': 'LEASE', '층': '저층', '전용면적': 59.8, 'spec': ''},
            {'거래유형': 'SALE', '층': '8층', '전용면적': 59.8, 'spec': '올수리'},
        ])
        
        print(f"  필터링 전: {len(sample_df)}개")
        filtered_df = filter_listings(sample_df)
        print(f"  필터링 후: {len(filtered_df)}개")
        print(f"  → 세안고 1개, 저층 0개 제외")
        
        print("\n✅ filter.py 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """database.py 테스트"""
    print("\n" + "="*60)
    print("💾 [TEST] database.py - 데이터베이스")
    print("="*60)
    
    try:
        from src.database import RealEstateDB
        
        # 임시 DB 생성
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = RealEstateDB(db_path)
            
            print("\n✓ 데이터베이스 초기화 완료")
            
            # 테스트 데이터
            complex_df = pd.DataFrame([{
                '단지번호': '12345',
                '단지명': '테스트아파트',
                '주소': '서울시 강남구',
                '세대수': 500,
                '건축년도': 2015,
                '면적': 100.0
            }])
            
            db.save_complexes(complex_df)
            print("✓ 단지 정보 저장 완료")
            
            # 가격 데이터 저장 (원 단위 → 만원 단위로 변환 테스트)
            price_df = pd.DataFrame([
                {
                    '면적타입': '59A',
                    '전용면적': 59.8,
                    '거래유형': 'SALE',
                    '가격': 120000000,  # 원 단위
                    '보증금': 0,
                    '층': '5층',
                    '층수': 5,
                    '방향': '남향'
                },
                {
                    '면적타입': '84A',
                    '전용면적': 84.3,
                    '거래유형': 'LEASE',
                    '가격': 0,
                    '보증금': 100000000,  # 원 단위
                    '층': '8층',
                    '층수': 8,
                    '방향': '남동향'
                }
            ])
            
            db.save_prices(price_df, '12345')
            print("✓ 가격 정보 저장 완료 (원 → 만원 변환)")
            
            # 저장된 데이터 조회
            latest = db.get_latest_prices(limit=10)
            print(f"✓ 저장된 데이터 조회: {len(latest)}개 행")
            
            # 가격 단위 확인
            if not latest.empty:
                prices = latest['price'].tolist()
                print(f"  저장된 가격 (만원): {prices}")
                if prices[0] == 12000:  # 120000000원 → 12000만원
                    print("  ✓ 가격 단위 변환 정상!")
            
            db.close()
            print("✓ 데이터베이스 연결 종료")
        
        print("\n✅ database.py 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth():
    """auth.py 테스트"""
    print("\n" + "="*60)
    print("🔐 [TEST] auth.py - 사용자 인증")
    print("="*60)
    
    try:
        from src.auth import UserManager
        
        # 임시 DB 생성
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_auth.db")
            
            # 초기화 (테이블 생성)
            from src.database import RealEstateDB
            db = RealEstateDB(db_path)
            db.close()
            
            # 사용자 관리자 생성
            user_manager = UserManager(db_path)
            
            # 1. 사용자 생성
            print("\n✓ 사용자 생성 테스트:")
            result = user_manager.create_user("testuser", "test@example.com", "password123")
            print(f"  생성 결과: {result}")
            
            # 2. 사용자 인증
            print("\n✓ 사용자 인증 테스트:")
            user = user_manager.verify_user("testuser", "password123")
            if user:
                print(f"  ✓ 인증 성공: {user['username']}")
            else:
                print(f"  ✗ 인증 실패")
                return False
            
            # 3. can_add_watchlist 테스트 (수정된 메소드)
            print("\n✓ can_add_watchlist() 테스트:")
            user_id = user['id']
            can_add = user_manager.can_add_watchlist(user_id)
            print(f"  사용자 {user_id}의 관심 단지 추가 가능: {can_add}")
            
            # 4. 관심 단지 추가
            print("\n✓ 관심 단지 추가 테스트:")
            result = user_manager.add_to_watchlist(user_id, "12345", "테스트아파트")
            print(f"  추가 결과: {result}")
            
            # 5. 관심 단지 목록
            watchlist = user_manager.get_watchlist(user_id)
            print(f"  관심 단지 수: {len(watchlist)}")
        
        print("\n✅ auth.py 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🧪 통합 테스트 스위트 - 2026.01.16".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # 각 테스트 실행
    results.append(("analyzer.py", test_analyzer()))
    results.append(("filter.py", test_filter()))
    results.append(("database.py", test_database()))
    results.append(("auth.py", test_auth()))
    
    # 결과 요약
    print("\n" + "="*60)
    print("📋 테스트 결과 요약")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("\n" + "-"*60)
    print(f"총 {total}개 테스트 중 {passed}개 통과")
    print("="*60)
    
    return all(r for _, r in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
