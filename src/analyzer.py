"""
네이버 부동산 가격 분석 모듈
Tampermonkey 스크립트의 getPrice_WeolbuStandard, sinhoCheck 재구현
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


# 신호등 기준값
SIGN_LOW_VALUE = 5   # 5% 미만: 녹색
SIGN_MIDDLE_VALUE = 10  # 10% 미만: 주황, 10% 이상: 빨강


def calculate_gap_and_ratio(sale_price: int, lease_price: int) -> Tuple[int, str]:
    """
    갭과 전세가율 계산
    
    Args:
        sale_price: 매매가 (만원)
        lease_price: 전세가 (만원)
    
    Returns:
        (갭, 전세가율) 튜플
        예: (18000, "85%")
    """
    if not sale_price or not lease_price:
        return (0, "-")
    
    gap = sale_price - lease_price
    ratio = int((lease_price / sale_price) * 100)
    
    return (gap, f"{ratio}%")


def signal_light_check(current_price: int, compare_price: int, multiplier: int = 1) -> Tuple[str, str]:
    """
    신호등 색상 결정 (Tampermonkey의 sinhoCheck 재구현)
    
    Args:
        current_price: 현재 가격 (만원)
        compare_price: 비교 가격 (만원)
        multiplier: 신호등 배율 (1, 2, 3)
    
    Returns:
        (색상, 툴팁) 튜플
        예: ('green', '3.5% / 5000')
    """
    if not current_price or not compare_price or compare_price <= current_price:
        return ('gray', '-')
    
    # 가격 차이 계산
    gap = compare_price - current_price
    
    # 퍼센트 계산 (100 - (낮은가 / 높은가 * 100))
    percentage = 100 - (current_price / compare_price * 100)
    
    tooltip = f"{percentage:.1f}% / {gap:,}만원"
    
    # 신호등 색상 결정
    if percentage < (SIGN_LOW_VALUE * multiplier):
        return ('green', tooltip)
    elif percentage <= (SIGN_MIDDLE_VALUE * multiplier):
        return ('orange', tooltip)
    else:
        return ('red', tooltip)


def get_price_summary_by_area(
    df: pd.DataFrame, 
    area_type: str,
    use_lowest_lease: bool = False
) -> Dict:
    """
    면적 타입별 가격 요약
    
    Args:
        df: 매물 DataFrame (가격은 만원 단위 저장됨)
        area_type: 면적 타입 (예: "59A", "84A")
        use_lowest_lease: True면 최저 전세, False면 최고 전세
    
    Returns:
        {
            'sale_min': 매매 최저가 (만원),
            'sale_floor': 매매 최저가 층,
            'sale_count': 매매 매물 수,
            'lease_max': 전세 최고/최저가 (만원),
            'lease_floor': 전세 층,
            'lease_count': 전세 매물 수,
            'gap': 갭 (만원),
            'lease_ratio': 전세가율 (문자열),
            'signal': 신호등 (색상, 툴팁)
        }
    
    주의: 모든 가격은 \"만원\" 단위로 반환됨
    """
    result = {
        'sale_min': 0,
        'sale_floor': '-',
        'sale_count': 0,
        'lease_max': 0,
        'lease_floor': '-',
        'lease_count': 0,
        'gap': 0,
        'lease_ratio': '-',
        'signal': ('gray', '-')
    }
    
    # 입력 데이터 검증
    if df is None or df.empty:
        return result
    
    # 해당 면적 타입만 필터링
    area_df = df[df['면적타입'] == area_type].copy()
    
    if area_df.empty:
        return result
    
    # 매매 데이터 처리
    sale_df = area_df[area_df['거래유형'] == 'SALE'].copy()
    if not sale_df.empty:
        # DB에서 조회한 가격은 이미 만원 단위
        # (만약 원 단위면 안전하게 변환)
        if sale_df['가격'].max() > 100000:  # 원 단위로 가정
            sale_df['가격_만원'] = sale_df['가격'] / 10000
        else:  # 이미 만원 단위
            sale_df['가격_만원'] = sale_df['가격']
        
        # 최저가 찾기
        min_idx = sale_df['가격_만원'].idxmin()
        result['sale_min'] = int(sale_df.loc[min_idx, '가격_만원'])
        result['sale_floor'] = sale_df.loc[min_idx, '층'] if '층' in sale_df.columns else '-'
        result['sale_count'] = len(sale_df)
    
    # 전세 데이터 처리
    lease_df = area_df[area_df['거래유형'] == 'LEASE'].copy()
    if not lease_df.empty:
        # DB에서 조회한 가격은 이미 만원 단위
        if lease_df['보증금'].max() > 100000:  # 원 단위로 가정
            lease_df['보증금_만원'] = lease_df['보증금'] / 10000
        else:  # 이미 만원 단위
            lease_df['보증금_만원'] = lease_df['보증금']
        
        # 최고가 또는 최저가
        if use_lowest_lease:
            target_idx = lease_df['보증금_만원'].idxmin()
        else:
            target_idx = lease_df['보증금_만원'].idxmax()
        
        result['lease_max'] = int(lease_df.loc[target_idx, '보증금_만원'])
        result['lease_floor'] = lease_df.loc[target_idx, '층'] if '층' in lease_df.columns else '-'
        result['lease_count'] = len(lease_df)
    
    # 갭과 전세가율 계산
    if result['sale_min'] > 0 and result['lease_max'] > 0:
        result['gap'], result['lease_ratio'] = calculate_gap_and_ratio(
            result['sale_min'], 
            result['lease_max']
        )
    
    return result


def calculate_price_per_pyeong(price: int, area_m2: float) -> int:
    """
    평당 가격 계산
    
    Args:
        price: 가격 (만원)
        area_m2: 전용면적 (m²)
    
    Returns:
        평당 가격 (만원/3.3m²)
    """
    if not area_m2 or area_m2 <= 0:
        return 0
    
    pyeong = area_m2 / 3.3
    return int(price / pyeong) if pyeong > 0 else 0


def get_all_area_summaries(
    df: pd.DataFrame, 
    use_lowest_lease: bool = False,
    signal_multiplier: int = 1
) -> Dict[str, Dict]:
    """
    모든 면적 타입별 가격 요약
    
    Args:
        df: 매물 DataFrame (가격은 만원 단위)
        use_lowest_lease: True면 최저 전세, False면 최고 전세
        signal_multiplier: 신호등 배율
    
    Returns:
        {
            '59A': {...},
            '84A': {...},
            ...
        }
    
    주의: 입력 df가 None 또는 비어있으면 빈 딕셔너리 반환
    """
    # 입력 데이터 검증
    if df is None or df.empty:
        return {}
    
    summaries = {}
    area_types = df['면적타입'].unique()
    
    if len(area_types) == 0:
        return {}
    
    for area_type in sorted(area_types):
        summary = get_price_summary_by_area(df, area_type, use_lowest_lease)
        
        # 신호등 계산 (같은 면적의 다음 가격과 비교)
        sale_df = df[(df['면적타입'] == area_type) & (df['거래유형'] == 'SALE')].copy()
        if len(sale_df) > 1 and summary['sale_min'] > 0:
            # 가격은 이미 만원 단위
            if sale_df['가격'].max() > 100000:  # 원 단위로 가정
                sale_df['가격_만원'] = sale_df['가격'] / 10000
            else:  # 이미 만원 단위
                sale_df['가격_만원'] = sale_df['가격']
            
            sorted_prices = sale_df['가격_만원'].sort_values().unique()
            
            # 최저가보다 비싼 첫 번째 가격 찾기
            higher_prices = [p for p in sorted_prices if p > summary['sale_min']]
            if higher_prices:
                next_price = higher_prices[0]
                summary['signal'] = signal_light_check(
                    summary['sale_min'], 
                    next_price, 
                    signal_multiplier
                )
        
        summaries[area_type] = summary
    
    return summaries


def format_price_display(price: int) -> str:
    """
    가격을 억/만원 형식으로 변환
    
    Args:
        price: 가격 (만원 단위)
    
    Returns:
        "12억 5000" 형식 문자열
    
    예시:
        120000 (만원) → "12억"
        120500 (만원) → "12억 500"
        5000 (만원) → "5,000"
        0 → "0"
    """
    if not isinstance(price, (int, float)):
        return "0"
    
    if price == 0:
        return "0"
    
    eok = int(price) // 10000
    man = int(price) % 10000
    
    if eok > 0 and man > 0:
        return f"{eok}억 {man:,}"
    elif eok > 0:
        return f"{eok}억"
    else:
        return f"{int(price):,}"


# 테스트 함수
if __name__ == "__main__":
    print("=== 가격 분석 모듈 테스트 ===\n")
    
    # 샘플 데이터 (만원 단위)
    test_data = [
        {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'SALE', '가격': 120000, '보증금': 0, '층': '5/10층'},
        {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'SALE', '가격': 125000, '보증금': 0, '층': '7/10층'},
        {'면적타입': '59A', '전용면적': 59.8, '거래유형': 'LEASE', '가격': 0, '보증금': 102000, '층': '8/10층'},
        {'면적타입': '84A', '전용면적': 84.3, '거래유형': 'SALE', '가격': 170000, '보증금': 0, '층': '6/12층'},
        {'면적타입': '84A', '전용면적': 84.3, '거래유형': 'LEASE', '가격': 0, '보증금': 145000, '층': '9/12층'},
    ]
    
    df = pd.DataFrame(test_data)
    
    # 전체 요약
    summaries = get_all_area_summaries(df, signal_multiplier=1)
    
    for area_type, summary in summaries.items():
        print(f"\n📊 {area_type}")
        print(f"  매매: {format_price_display(summary['sale_min'])} ({summary['sale_floor']}) - {summary['sale_count']}개")
        print(f"  전세: {format_price_display(summary['lease_max'])} ({summary['lease_floor']}) - {summary['lease_count']}개")
        print(f"  갭: {format_price_display(summary['gap'])}")
        print(f"  전세가율: {summary['lease_ratio']}")
        print(f"  신호등: {summary['signal'][0]} - {summary['signal'][1]}")
