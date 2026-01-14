"""
네이버 부동산 매물 필터링 로직
Tampermonkey 스크립트의 checkItemCondition, checkMandantoryCondition 재구현
"""

import re
import pandas as pd
from typing import Dict, Optional, Tuple


def parse_floor(floor_str: str) -> Tuple[int, int]:
    """
    층수 문자열 파싱 (Tampermonkey의 getFloor 함수 재구현)
    
    Args:
        floor_str: "5/10층", "중층(6~12층)", "저층" 등
    
    Returns:
        (현재층, 총층수) 튜플
    
    Examples:
        "5/10층" -> (5, 10)
        "저층" -> (3, 10)  # 추정값
        "고층(13층 이상)" -> (15, 20)
    """
    if not floor_str:
        return (0, 0)
    
    # "5/10층" 형식
    match = re.search(r'(\d+)/(\d+)', floor_str)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    
    # "저층" - 1~5층 추정
    if '저' in floor_str or '저층' in floor_str:
        return (3, 10)
    
    # "중층" - 6~12층 추정
    if '중' in floor_str or '중층' in floor_str:
        return (9, 15)
    
    # "고층" - 13층 이상 추정
    if '고' in floor_str or '고층' in floor_str:
        return (15, 20)
    
    # "5층" 형식 (총층수 불명)
    match = re.search(r'(\d+)층', floor_str)
    if match:
        floor_num = int(match.group(1))
        return (floor_num, floor_num + 5)  # 총층수 추정
    
    return (0, 0)


def check_seango_spec(spec: str) -> bool:
    """
    세안고/끼고 매물 여부 확인
    
    Args:
        spec: 매물 특이사항 (예: "세입자끼고", "전세안고", "승계")
    
    Returns:
        True면 세안고 매물
    """
    if not spec:
        return False
    
    seango_keywords = ['끼고', '안고', '승계', '세안고', '세입자']
    return any(keyword in spec for keyword in seango_keywords)


def check_low_floor_exclusion(floor: str, trade_type: str) -> bool:
    """
    저층 제외 로직 (Tampermonkey의 checkItemCondition 재구현)
    
    Args:
        floor: 층수 문자열 (예: "5/10층")
        trade_type: 거래 유형 ("SALE" or "LEASE")
    
    Returns:
        True면 제외 대상
    """
    current_floor, total_floor = parse_floor(floor)
    
    # 전세는 층 관계없이 허용
    if trade_type == "LEASE":
        return False
    
    # 매매의 경우
    if trade_type == "SALE":
        # 층수 불명확한 경우 제외
        if current_floor == 0:
            return True
        
        # 저층 표기 제외
        if '저' in floor:
            return True
        
        # 1층, 2층, 3층 제외
        if current_floor in [1, 2, 3]:
            return True
        
        # 탑층 제외 (현재층 == 총층수)
        if current_floor > 0 and current_floor == total_floor:
            return True
        
        # 5층 이상 건물에서 3층 이하 제외
        if total_floor >= 5 and current_floor <= 3:
            return True
    
    return False


def check_area_exclusion(area_m2: float, max_pyeong: int = 35) -> bool:
    """
    면적 제외 로직
    
    Args:
        area_m2: 전용면적 (m²)
        max_pyeong: 최대 평수 (기본 35평)
    
    Returns:
        True면 제외 대상 (제한 평수 초과)
    """
    pyeong = area_m2 / 3.3
    return pyeong > max_pyeong


def filter_listings(
    df: pd.DataFrame, 
    options: Optional[Dict] = None
) -> pd.DataFrame:
    """
    매물 DataFrame 필터링
    
    Args:
        df: 매물 DataFrame (컬럼: 거래유형, 층, 전용면적, spec 등)
        options: 필터링 옵션
            - exclude_seango: 세안고 제외 (기본 True)
            - exclude_low_floors: 저층 제외 (기본 True)
            - max_area_pyeong: 최대 평수 (기본 35평)
            - include_large_area: 큰 평수 포함 (기본 False)
    
    Returns:
        필터링된 DataFrame
    """
    if df is None or df.empty:
        return df
    
    # 기본 옵션
    default_options = {
        'exclude_seango': True,
        'exclude_low_floors': True,
        'max_area_pyeong': 35,
        'include_large_area': False,
    }
    
    if options:
        default_options.update(options)
    
    filtered = df.copy()
    
    # 1. 세안고 제외
    if default_options['exclude_seango'] and 'spec' in filtered.columns:
        before_count = len(filtered)
        filtered = filtered[~filtered['spec'].apply(check_seango_spec)]
        removed = before_count - len(filtered)
        if removed > 0:
            print(f"  ✓ 세안고 매물 {removed}개 제외")
    
    # 2. 저층/탑층 제외 (매매만)
    if default_options['exclude_low_floors'] and '층' in filtered.columns and '거래유형' in filtered.columns:
        before_count = len(filtered)
        filtered = filtered[
            ~filtered.apply(
                lambda row: check_low_floor_exclusion(row['층'], row['거래유형']), 
                axis=1
            )
        ]
        removed = before_count - len(filtered)
        if removed > 0:
            print(f"  ✓ 저층/탑층 매물 {removed}개 제외")
    
    # 3. 면적 제외 (35평 이상)
    if not default_options['include_large_area'] and '전용면적' in filtered.columns:
        before_count = len(filtered)
        filtered = filtered[
            ~filtered['전용면적'].apply(
                lambda x: check_area_exclusion(x, default_options['max_area_pyeong'])
            )
        ]
        removed = before_count - len(filtered)
        if removed > 0:
            print(f"  ✓ {default_options['max_area_pyeong']}평 초과 매물 {removed}개 제외")
    
    return filtered


def get_filter_summary(df_before: pd.DataFrame, df_after: pd.DataFrame) -> str:
    """
    필터링 요약 문자열 생성
    
    Returns:
        "전체 100개 → 필터링 후 75개 (25개 제외)"
    """
    before = len(df_before) if df_before is not None else 0
    after = len(df_after) if df_after is not None else 0
    removed = before - after
    
    return f"전체 {before}개 → 필터링 후 {after}개 ({removed}개 제외)"


# 테스트 함수
if __name__ == "__main__":
    print("=== 필터링 모듈 테스트 ===\n")
    
    # 샘플 데이터
    test_data = [
        {'거래유형': 'SALE', '층': '5/10층', '전용면적': 59.8, 'spec': '정상입주'},
        {'거래유형': 'SALE', '층': '2/10층', '전용면적': 84.3, 'spec': '확장올수리'},  # 2층 제외
        {'거래유형': 'SALE', '층': '10/10층', '전용면적': 59.8, 'spec': '정상입주'},  # 탑층 제외
        {'거래유형': 'LEASE', '층': '1/10층', '전용면적': 84.3, 'spec': '정상입주'},  # 전세는 OK
        {'거래유형': 'SALE', '층': '7/12층', '전용면적': 120.5, 'spec': '정상입주'},  # 36평 제외
        {'거래유형': 'SALE', '층': '8/15층', '전용면적': 84.3, 'spec': '세입자끼고'},  # 세안고 제외
    ]
    
    df = pd.DataFrame(test_data)
    print(f"원본 데이터: {len(df)}개\n")
    print(df[['거래유형', '층', '전용면적', 'spec']])
    
    # 필터링 적용
    print("\n\n필터링 적용중...")
    filtered = filter_listings(df)
    
    print(f"\n\n필터링 결과: {len(filtered)}개\n")
    print(filtered[['거래유형', '층', '전용면적', 'spec']])
    
    print(f"\n{get_filter_summary(df, filtered)}")
