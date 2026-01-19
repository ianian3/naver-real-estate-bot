# Streamlit Cloud 배포 가이드

## 🚀 베타 런칭 준비

### 1단계: Streamlit Cloud 계정 생성

1. https://streamlit.io/cloud 접속
2. GitHub으로 로그인
3. 무료 플랜 선택

### 2단계: 앱 배포

**Streamlit Cloud 대시보드에서:**

1. **New app** 클릭
2. **Repository**: `ianian3/naver-real-estate-bot`
3. **Branch**: `main`
4. **Main file path**: `app.py`
5. **App URL**: 원하는 URL 선택 (예: `naver-real-estate-bot`)

### 3단계: 환경변수 설정

**Advanced settings > Secrets**에 추가:

```toml
# .streamlit/secrets.toml 형식
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
```

### 4단계: 배포!

**Deploy** 버튼 클릭 → 자동으로 배포됩니다.

---

## 📋 배포 전 체크리스트

### 필수 파일 확인

- [x] `requirements.txt` - 모든 의존성 포함
- [x] `app.py` - 메인 애플리케이션
- [x] `.gitignore` - `.env` 파일 제외
- [x] `README.md` - 프로젝트 설명

### 데이터베이스

**SQLite 주의사항:**
- Streamlit Cloud는 매 배포 시 파일 시스템 초기화
- 데이터베이스는 재시작 시 **모두 삭제됨**

**해결 방법:**
1. **단기**: 각 사용자가 데이터 재업로드
2. **장기**: PostgreSQL (Supabase 무료 티어 사용 권장)

---

## 🔧 배포 후 설정

### 1. 도메인 연결 (선택사항)

Streamlit Cloud 무료 플랜은 커스텀 도메인 미지원.
프로 플랜($20/월)으로 업그레이드 필요.

### 2. 사용량 모니터링

**Streamlit Cloud 무료 플랜 제한:**
- 1개 private 앱
- 무제한 public 앱
- 1GB RAM
- 1CPU

### 3. 로그 확인

Streamlit Cloud 대시보드 → **Logs** 탭

---

## 🎯 베타 테스트 준비

### 테스터 모집 방법

1. **GitHub README에 배포 URL 추가**
2. **소셜 미디어 공유**:
   - 네이버 카페 (부동산 커뮤니티)
   - 페이스북 그룹
   - 인스타그램
3. **피드백 수집**:
   - GitHub Issues
   - Google Forms

### 베타 테스터 안내사항

```markdown
🎉 **베타 테스터 모집!**

네이버 부동산 분석 서비스 베타 테스터를 모집합니다.

**서비스 URL**: https://your-app.streamlit.app

**제공 기능:**
- 아파트 시세 분석
- 투자금 자동 계산
- 가격 변동 알림 (이메일)

**참여 방법:**
1. 위 URL 접속
2. 회원가입
3. 서비스 사용
4. 피드백 제출 (GitHub Issues)

**베타 특전:**
- 영구 무료 사용 (정식 출시 후에도)
- 우선 기능 요청 반영

기간: 2026년 1월 ~ 2월
```

---

## 🐛 트러블슈팅

### 배포가 실패해요

**확인사항:**
1. `requirements.txt` 패키지 버전 충돌 확인
2. Python 버전 확인 (3.9+ 권장)
3. 로그에서 오류 메시지 확인

**해결:**
```bash
# 로컬에서 테스트
pip install -r requirements.txt
streamlit run app.py
```

### 앱이 느려요

**최적화:**
1. `@st.cache_data` 적극 활용
2. DB 쿼리 최소화
3. 큰 데이터는 pagination

### 데이터베이스가 계속 초기화돼요

**영구 스토리지 필요:**
- Supabase (무료)
- Railway (무료 티어)
- PlanetScale (무료)

---

## 📊 성공 지표

**베타 기간 목표 (1개월):**
- 회원가입: 100명
- 활성 사용자: 50명
- 피드백: 20건 이상
- 버그 리포트: 수집 및 수정

---

## 🔄 업데이트 배포

GitHub에 push하면 **자동으로 재배포**됩니다!

```bash
git add .
git commit -m "fix: Bug fixes"
git push origin main
```

약 2-3분 후 업데이트 완료.

---

## 📞 지원

문제가 있다면:
- Streamlit 문서: https://docs.streamlit.io/
- 커뮤니티: https://discuss.streamlit.io/
