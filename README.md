# 네이버 부동산 크롤링 Bot 🏢

네이버 부동산 데이터를 자동으로 수집하고 분석하는 시스템입니다. Tampermonkey 스크립트의 필터링 로직을 Python으로 구현하여 브라우저 자동화 및 데이터 시각화를 제공합니다.

## ✨ 주요 기능

### 1. **Tampermonkey 필터링 로직 통합**
- ✅ 세안고/끼고 매물 자동 제외
- ✅ 1-3층, 저층, 탑층 필터링 (매매만 적용)
- ✅ 35평 이상 제외 옵션
- ✅ 신호등 시스템 (가격 비교 색상 표시)

### 2. **브라우저 자동화 (Playwright)**
- 네이버 부동산 페이지 자동 접근
- JavaScript 실행으로 DOM 데이터 추출
- 매물 스크롤 및 로드 자동화
- API 429 에러 우회

### 3. **가격 분석 모듈**
- 면적별 최저 매매가/최고 전세가 계산
- 전세가율, 갭 자동 계산
- 평당 가격 산출
- 신호등 색상 결정 (5%, 10% 기준)

### 4. **데이터 시각화 (Streamlit)**
- 매물 리스트 필터링
- 평형별 가격 분석 차트
- 아파트별 통계
- CSV 내보내기

---

## 📁 프로젝트 구조

```
naver_real_estage_bot/
├── main.py                    # 메인 실행 파일 (데이터 수집)
├── app.py                     # Streamlit UI (시각화)
├── import_json.py             # Tampermonkey JSON 가져오기
├── requirements.txt           # 패키지 의존성
├── memo                       # 원본 Tampermonkey 스크립트
├── tampermonkey_export.js     # 브라우저 스크립트 (수동 내보내기)
│
├── src/
│   ├── filter.py              # ⭐ 필터링 로직 (세안고, 층수, 면적)
│   ├── analyzer.py            # ⭐ 가격 분석 (신호등, 갭, 전세가율)
│   ├── browser_scraper.py     # ⭐ Playwright 브라우저 자동화
│   ├── crawler.py             # API + 샘플 데이터 생성
│   ├── scraper.py             # 네이버 API 호출
│   └── database.py            # SQLite DB 관리
│
└── data/
    └── real_estate.db         # 수집된 데이터 저장
```

---

## 🚀 설치 및 실행

### 1. 가상환경 설정
```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. 데이터 수집

#### 옵션 A: 샘플 데이터로 테스트 (기본)
```bash
python main.py
```

#### 옵션 B: 브라우저 자동화 사용
`main.py` 파일을 열어 다음과 같이 수정:
```python
USE_BROWSER_SCRAPING = True  # False → True로 변경
HEADLESS = False  # 브라우저 창을 보고 싶으면 False
```

```bash
python main.py
```

### 4. Streamlit UI 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 🎯 사용 방법

### 방법 1: 자동 크롤링 (추천)

1. `main.py`에서 `USE_BROWSER_SCRAPING = True` 설정
2. `python main.py` 실행
3. 브라우저가 자동으로 네이버 부동산에 접속하여 데이터 수집
4. `streamlit run app.py`로 결과 확인

### 방법 2: Tampermonkey 수동 내보내기

1. 브라우저에 Violentmonkey/Tampermonkey 설치
2. `tampermonkey_export.js` 스크립트 등록
3. 네이버 부동산 페이지에서 "📥 Python으로 내보내기" 버튼 클릭
4. JSON 파일 다운로드
5. `python import_json.py data/naver_XXX.json` 실행
6. `streamlit run app.py`로 결과 확인

---

## ⚙️ 설정

### 필터링 옵션 (`src/filter.py`)

```python
filter_options = {
    'exclude_seango': True,      # 세안고/끼고 제외
    'exclude_low_floors': True,  # 1-3층, 탑층 제외
    'max_area_pyeong': 35,       # 최대 평수
    'include_large_area': False, # 35평 초과 포함 여부
}
```

### 신호등 배율 (`src/analyzer.py`)

```python
SIGN_LOW_VALUE = 5   # 5% 미만: 녹색
SIGN_MIDDLE_VALUE = 10  # 10% 미만: 주황, 10% 이상: 빨강
```

### 브라우저 설정 (`main.py`)

```python
USE_BROWSER_SCRAPING = False  # True: 브라우저 자동화 사용
HEADLESS = True               # False: 브라우저 UI 표시
```

---

## 🛠️ 모듈별 기능

### `src/filter.py` - 필터링 로직
- `parse_floor()`: 층수 문자열 파싱
- `check_seango_spec()`: 세안고 매물 확인
- `check_low_floor_exclusion()`: 저층/탑층 제외
- `filter_listings()`: DataFrame 필터링

### `src/analyzer.py` - 가격 분석
- `calculate_gap_and_ratio()`: 갭, 전세가율 계산
- `signal_light_check()`: 신호등 색상 결정
- `get_price_summary_by_area()`: 면적별 가격 요약
- `get_all_area_summaries()`: 전체 요약

### `src/browser_scraper.py` - 브라우저 자동화
- `NaverRealEstateScraper`: Playwright 기반 스크래퍼
- `navigate_to_complex()`: 단지 페이지 이동
- `scroll_article_list()`: 매물 리스트 스크롤
- `extract_listings()`: DOM 데이터 추출

---

## 📊 Streamlit UI 기능

### 사이드바 필터
- ✅ **세안고/끼고 제외**: 세입자끼고, 전세안고 매물 필터링
- ✅ **저층/탑층 제외**: 1-3층, 탑층 제외 (매매만)
- 🚦 **신호등 배율**: X1, X2, X3 선택

### 탭별 기능
- **📋 매물 리스트**: 전체 매물 테이블 (정렬 가능)
- **📊 가격 분석**: 평형별 통계 및 차트
- **🏢 아파트별 통계**: 단지별 평균 가격
- **💾 내보내기**: CSV 다운로드

---

## 🧪 테스트

### 1. 필터링 모듈 테스트
```bash
source venv/bin/activate
python src/filter.py
```

**예상 출력:**
```
=== 필터링 모듈 테스트 ===
원본 데이터: 6개
필터링 적용중...
  ✓ 세안고 매물 1개 제외
  ✓ 저층/탑층 매물 2개 제외
  ✓ 35평 초과 매물 1개 제외
필터링 결과: 2개
```

### 2. 가격 분석 모듈 테스트
```bash
python src/analyzer.py
```

**예상 출력:**
```
=== 가격 분석 모듈 테스트 ===

📊 59A
  매매: 12억 (5/10층) - 2개
  전세: 10억 2,000 (8/10층) - 1개
  갭: 1억 8,000
  전세가율: 85%
  신호등: green - 4.0% / 5,000만원
```

### 3. 전체 시스템 테스트
```bash
python main.py
streamlit run app.py
```

---

## 📝 데이터베이스 스키마

### `complexes` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| complex_no | TEXT | 단지번호 (PK) |
| complex_name | TEXT | 단지명 |
| address | TEXT | 주소 |
| total_households | INTEGER | 세대수 |
| build_year | INTEGER | 건축년도 |

### `prices` 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | ID (PK, AUTO) |
| complex_no | TEXT | 단지번호 (FK) |
| area_type | TEXT | 면적타입 (59A, 84A) |
| exclusive_area | REAL | 전용면적 (m²) |
| transaction_type | TEXT | 거래유형 (SALE/LEASE) |
| price | INTEGER | 가격 (원) |
| deposit | INTEGER | 보증금 (원) |
| floor | TEXT | 층 ("5/10층") |
| floor_number | INTEGER | 층수 (5) |
| spec | TEXT | 특이사항 (세안고 등) |
| collected_at | TEXT | 수집일시 |

---

## 🚨 주의사항

1. **네이버 부동산 이용약관**: 과도한 크롤링은 차단될 수 있습니다
2. **Rate Limiting**: `main.py`에서 `time.sleep()` 조정 필요
3. **브라우저 자동화**: Playwright는 브라우저를 실제로 실행하므로 느립니다
4. **데이터 정확성**: 샘플 데이터는 테스트용이며 실제 데이터와 다릅니다

---

## 🔧 트러블슈팅

### 1. Playwright 설치 오류
```bash
pip uninstall playwright
pip install playwright
playwright install chromium
```

### 2. DB 초기화
```bash
rm data/real_estate.db
python main.py
```

### 3. SSL 경고 무시
```python
import warnings
warnings.filterwarnings('ignore')
```

---

## 📚 참고자료

- [네이버 부동산](https://new.land.naver.com/)
- [Playwright 문서](https://playwright.dev/python/)
- [Streamlit 문서](https://docs.streamlit.io/)
- [Tampermonkey](https://www.tampermonkey.net/)

---

## 📄 라이선스

MIT License

---

## 👨‍💻 작성자

- Tampermonkey 스크립트: 모느나
- Python 통합: AI Assistant
- 버전: 1.0.0
- 업데이트: 2026-01-13
