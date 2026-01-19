"""
AI 투자 분석 보고서 생성 모듈
Google Gemini API를 사용하여 저환수원리 기반 투자 분석 보고서 생성
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def generate_investment_report(analysis_data: dict) -> str:
    """
    저환수원리 분석 데이터를 기반으로 AI 투자 분석 보고서 생성
    
    Args:
        analysis_data: {
            'target_name': 단지명,
            'target_area': 면적,
            'target_sale': 매매가(만원),
            'target_lease': 전세가(만원),
            'scores': {'저': 점수, '환': 점수, ...},
            'total_score': 종합점수,
            'grade': 등급,
            'recommendation': 추천의견,
            'details': {
                'underval_comment': 저평가 코멘트,
                'liquidity_checks': 환금성 체크항목,
                'roi': 예상수익률,
                'lease_ratio': 전세가율,
                'supply_grade': 입주물량등급,
                'build_age': 연식
            }
        }
    
    Returns:
        str: 마크다운 형식의 분석 보고서
    """
    
    # API 키 확인
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    
    if api_key:
        return _generate_with_gemini(analysis_data, api_key)
    else:
        # API 키가 없으면 템플릿 기반 보고서 생성
        return _generate_template_report(analysis_data)


def _generate_with_gemini(analysis_data: dict, api_key: str) -> str:
    """Gemini API를 사용한 보고서 생성"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = _build_prompt(analysis_data)
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return _generate_template_report(analysis_data)


def _build_prompt(data: dict) -> str:
    """AI 프롬프트 생성"""
    
    target = data.get('target_name', '대상 단지')
    area = data.get('target_area', '84m²')
    sale = data.get('target_sale', 0)
    lease = data.get('target_lease', 0)
    scores = data.get('scores', {})
    total = data.get('total_score', 50)
    grade = data.get('grade', '★★★☆☆')
    recommendation = data.get('recommendation', '검토 필요')
    details = data.get('details', {})
    
    gap = sale - lease if sale and lease else 0
    lease_ratio = (lease / sale * 100) if sale else 0
    
    prompt = f"""
당신은 부동산 투자 전문 애널리스트입니다. 
월급쟁이부자들(월부)의 '저환수원리' 투자 원칙에 기반하여 다음 아파트에 대한 상세 투자 분석 보고서를 작성해주세요.

## 분석 대상
- 단지명: {target}
- 면적: {area}
- 매매가: {sale:,}만원 ({sale/10000:.1f}억)
- 전세가: {lease:,}만원 ({lease/10000:.1f}억)
- 투자금(갭): {gap:,}만원 ({gap/10000:.1f}억)
- 전세가율: {lease_ratio:.1f}%

## 저환수원리 점수
- 저(저평가): {scores.get('저', 50)}점 - {details.get('underval_comment', '분석 필요')}
- 환(환금성): {scores.get('환', 50)}점
- 수(수익률): {scores.get('수', 50)}점 - 예상 ROI {details.get('roi', 0):.0f}%
- 원(원금보존): {scores.get('원', 50)}점 - 전세가율 {lease_ratio:.1f}%
- 리(리스크): {scores.get('리', 50)}점 - 입주물량 {details.get('supply_grade', 'B')}, {details.get('build_age', 10)}년차

## 종합 평가
- 종합 점수: {total:.0f}점
- 등급: {grade}
- 투자 의견: {recommendation}

---

위 정보를 바탕으로 다음 형식의 투자 분석 보고서를 작성해주세요:

1. **종합 평가 요약** (2-3문장)
2. **저평가 분석** - 현재 가격 수준 평가
3. **환금성 분석** - 매도 시 유동성 전망
4. **수익률 전망** - 시나리오별 예상 수익 (보수적/중립/낙관적)
5. **원금보존 분석** - 역전세 리스크, 전세가율 평가
6. **리스크 요인** - 입주물량, 금리, 정책 등
7. **투자 전략 추천** - 매수 타이밍, 보유 기간, 출구 전략
8. **결론** (3-4문장의 최종 투자 의견)

보고서는 한국어로, 전문적이면서도 이해하기 쉽게 작성해주세요.
마지막에 "본 보고서는 투자 참고용이며 투자 권유가 아닙니다"라는 면책 조항을 포함하세요.
"""
    
    return prompt


def _generate_template_report(data: dict) -> str:
    """API 없이 템플릿 기반 보고서 생성"""
    
    target = data.get('target_name', '대상 단지')
    area = data.get('target_area', '84m²')
    sale = data.get('target_sale', 0)
    lease = data.get('target_lease', 0)
    scores = data.get('scores', {})
    total = data.get('total_score', 50)
    grade = data.get('grade', '★★★☆☆')
    recommendation = data.get('recommendation', '검토 필요')
    details = data.get('details', {})
    
    gap = sale - lease if sale and lease else 0
    lease_ratio = (lease / sale * 100) if sale else 0
    roi = details.get('roi', 0)
    
    # 점수 기반 평가 문구 생성
    underval_score = scores.get('저', 50)
    if underval_score >= 70:
        underval_eval = "현재 주변 시세 대비 저평가 구간에 있어 매수 매력이 있습니다."
    elif underval_score >= 50:
        underval_eval = "현재 가격은 적정 수준으로 판단됩니다."
    else:
        underval_eval = "현재 주변 시세 대비 다소 고평가된 상태입니다."
    
    principal_score = scores.get('원', 50)
    if principal_score >= 70:
        principal_eval = "전세가율이 안정적이어서 역전세 위험이 낮습니다."
    elif principal_score >= 50:
        principal_eval = "전세가율이 다소 높아 시장 변동에 주의가 필요합니다."
    else:
        principal_eval = "전세가율이 높아 역전세 가능성에 대비해야 합니다."
    
    report = f"""
# 📊 투자 분석 보고서

**분석일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}

---

## 1. 분석 대상

| 항목 | 내용 |
|------|------|
| 단지명 | {target} |
| 면적 | {area} |
| 매매가 | {sale:,}만원 ({sale/10000:.1f}억) |
| 전세가 | {lease:,}만원 ({lease/10000:.1f}억) |
| 투자금(갭) | {gap:,}만원 ({gap/10000:.1f}억) |
| 전세가율 | {lease_ratio:.1f}% |

---

## 2. 종합 평가

### {grade} 종합 {total:.0f}점 - {recommendation}

{target}은(는) 저환수원리 분석 기준 **{total:.0f}점**으로 **{recommendation}** 등급입니다.

---

## 3. 세부 분석

### 🟢 저평가 분석 ({scores.get('저', 50)}점)
{underval_eval}
{details.get('underval_comment', '')}

### 🟡 환금성 분석 ({scores.get('환', 50)}점)
선택된 조건 {details.get('liquidity_checks', 0)}개 충족. 
{'대형 단지로 거래 활발, 매도 시 유동성 양호' if scores.get('환', 50) >= 70 else '매도 시 적정 기간 소요 예상'}

### 🟢 수익률 전망 ({scores.get('수', 50)}점)
- **투자금(갭)**: {gap/10000:.1f}억
- **예상 수익률**: {roi:.0f}%

| 시나리오 | 예상 수익 | 기간 |
|----------|----------|------|
| 보수적 | +{max(roi*0.5, 10):.0f}% | 3년 |
| 중립 | +{max(roi*0.8, 20):.0f}% | 2년 |
| 낙관적 | +{roi:.0f}% | 1-2년 |

### 🟡 원금보존 분석 ({scores.get('원', 50)}점)
- **전세가율**: {lease_ratio:.1f}%
- {principal_eval}

### 🔴 리스크 요인 ({scores.get('리', 50)}점)
- **입주물량**: {details.get('supply_grade', 'B등급').split(':')[0] if ':' in str(details.get('supply_grade', 'B')) else details.get('supply_grade', 'B')}등급
- **연식**: {details.get('build_age', 10)}년차
- **금리 리스크**: 현 금리 수준 유지 시 안정적

---

## 4. 투자 전략 추천

### 매수 전략
{'- 현재 가격에서 즉시 매수 고려 가능' if total >= 70 else '- 추가 가격 조정 시 매수 검토'}
- 급매물 우선 검토 권장

### 보유 전략
- 예상 보유 기간: {'1-2년' if total >= 70 else '2-3년'}
- 전세 만기 관리 철저히

### 출구 전략
- 전고점 회복 시 부분 익절 고려
- 시장 과열 시 전체 매도 검토

---

## 5. 결론

{target} {area}는 저환수원리 기준 **{grade}** 등급으로, 
{'투자 매력이 높은 물건입니다. 적극적인 매수를 고려해볼 만합니다.' if total >= 70 else '신중한 검토가 필요합니다. 추가적인 현장 조사와 시세 확인을 권장합니다.' if total >= 50 else '현재 시점에서는 투자를 보류하고 시장 상황을 지켜볼 것을 권장합니다.'}

---

> ⚠️ **면책 조항**: 본 보고서는 투자 참고용이며 투자 권유가 아닙니다. 
> 실제 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
> 부동산 시장은 다양한 변수에 영향을 받으므로 전문가 상담을 권장합니다.
"""
    
    return report
