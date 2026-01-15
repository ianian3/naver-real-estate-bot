# 🚀 Naver Real Estate Analysis# 네이버 부동산 분석 서비스

> 🎉 **베타 버전 출시!** - 부동산 투자를 데이터로 시작하세요

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**배포 URL**: [https://your-app.streamlit.app](https://streamlit.io/cloud) _(배포 후 업데이트)_

---

## ⚡ 빠른 시작 (베타 테스터)

## 📊 주요 기능

- **Streamlit 웹 UI**: 직관적인 데이터 시각화
- **Tampermonkey 스크립트**: 네이버 부동산에서 데이터 추출
- **JSON 파일 업로드**: 브라우저에서 직접 데이터 가져오기
- **면적별 가격 분석**: 59m², 75m², 84m² 분석
- **투자금 계산**: 매매가 - 전세가 자동 계산
- **아파트별 차트**: 면적별 분리된 시각화
- **SQLite 데이터베이스**: 효율적인 데이터 저장

## 🛠️ 설치 방법

### 1. 저장소 복제
```bash
git clone https://github.com/ianian3/naver-real-estate-bot.git
cd naver-real-estate-bot
```

### 2. 가상환경 생성 및 활성화
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 실행
```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속

## 📝 사용 방법

### Tampermonkey 스크립트 설치
1. Violentmonkey 또는 Tampermonkey 브라우저 확장 설치
2. `tampermonkey_export.js` 파일 내용 복사
3. 새 스크립트 생성 후 붙여넣기
4. 저장

### 데이터 수집
1. 네이버 부동산 아파트 페이지 방문
2. 우측 상단 "📥 Python으로 내보내기" 버튼 클릭
3. JSON 파일 다운로드

### Streamlit에서 분석
1. 좌측 사이드바 "📥 데이터 가져오기"
2. JSON 파일 업로드
3. 자동으로 DB 저장 및 시각화

## 📂 프로젝트 구조

```
naver-real-estate-bot/
├── app.py                    # Streamlit UI
├── main.py                   # 메인 실행 파일
├── import_json.py            # JSON 가져오기
├── tampermonkey_export.js    # Tampermonkey 스크립트
├── requirements.txt          # Python 패키지
├── src/
│   ├── database.py          # SQLite DB 관리
│   ├── filter.py            # 필터링 로직
│   ├── analyzer.py          # 가격 분석
│   ├── crawler.py           # 크롤링 (샘플)
│   └── browser_scraper.py   # Playwright 스크래핑
├── data/
│   └── real_estate.db       # SQLite 데이터베이스
├── README.md                # 이 파일
└── SETUP.md                 # 다른 PC 설정 가이드
```

## 🔄 다른 컴퓨터에서 작업하기

자세한 내용은 [SETUP.md](SETUP.md) 참조

**최신 버전 받기:**
```bash
git pull
```

**변경사항 업로드:**
```bash
git add .
git commit -m "작업 내용"
git push
```

## 📊 화면 구성

- **매물 리스트**: 전체 매물 데이터 테이블
- **면적별 가격 분석**: 
  - 매매가/전세가 통계
  - 59m², 84m² 아파트별 차트
  - 투자금 계산 (매매가-전세가)
- **아파트별 현황**: 단지별 상세 정보

## 🛡️ 주의사항

- `venv/`, `__pycache__/`, `*.db` 파일은 Git에 포함되지 않습니다
- DB 파일은 로컬에서만 유지됩니다
- 개인 정보가 포함된 데이터는 업로드하지 마세요

## 📄 라이선스

개인 프로젝트

## 👤 개발자

ianian3
