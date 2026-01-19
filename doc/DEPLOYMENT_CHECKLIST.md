# Streamlit Cloud 배포 체크리스트

## ✅ 배포 전 준비 완료

- [x] 모든 코드 Git 커밋
- [x] Git push origin main
- [x] 법적 문서 (이용약관, 개인정보처리방침)
- [x] FAQ 작성
- [x] requirements.txt 확인
- [x] .gitignore 설정 (.env 제외)

---

## 🚀 Streamlit Cloud 배포 단계

### 1단계: Streamlit Cloud 접속
👉 https://streamlit.io/cloud

**로그인:**
- "Sign in with GitHub" 클릭
- GitHub 계정으로 로그인 (ianian3)

### 2단계: 새 앱 생성
1. **"New app"** 버튼 클릭
2. 다음 정보 입력:

   ```
   Repository: ianian3/naver-real-estate-bot
   Branch: main
   Main file path: app.py
   ```

3. **App URL** 설정:
   ```
   추천: naver-real-estate-analysis
   → URL: https://naver-real-estate-analysis.streamlit.app
   ```

### 3단계: 환경변수 설정 (중요!)

**Advanced settings** 클릭 → **Secrets** 탭

다음 내용 입력:
```toml
# Email settings for notifications
EMAIL_ADDRESS = "your-email@gmail.com"
EMAIL_PASSWORD = "your-16-digit-app-password"
```

⚠️ **주의:**
- Gmail 앱 비밀번호 사용 (계정 비밀번호 아님)
- 16자리 공백 포함 문자열
- 발급 방법: `EMAIL_SETUP.md` 참고

### 4단계: 배포!

**"Deploy!"** 버튼 클릭

⏱️ **배포 시간:** 약 2-3분

---

## 📊 배포 후 확인사항

### 즉시 확인
- [ ] 앱이 정상 로드되는가?
- [ ] 로그인/회원가입 작동하는가?
- [ ] 데이터 업로드 기능 작동하는가?
- [ ] 에러 메시지가 없는가?

### 기능 테스트
- [ ] 회원가입 → 로그인
- [ ] JSON 파일 업로드
- [ ] 관심 단지 추가/제거
- [ ] 데이터 필터링 (전체/관심)
- [ ] 테스트 이메일 발송

### 문제 발생 시
**Streamlit Cloud 대시보드:**
- Manage app → **Logs** 탭에서 오류 확인
- **Reboot** 버튼으로 재시작

---

## 🎉 배포 완료 후 작업

### 1. README 업데이트

**배포 URL 추가:**
```bash
# README.md 상단에
**배포 URL**: https://[your-app-name].streamlit.app
```

### 2. 베타 테스터 모집

**공유 채널:**
- [ ] GitHub README에 배포 URL 추가
- [ ] 네이버 카페 (부동산 투자 커뮤니티)
- [ ] 페이스북 부동산 그룹
- [ ] 오픈 카카오톡

**모집 메시지 템플릿:**
```markdown
🎉 부동산 시세 분석 서비스 베타 테스터 모집!

📊 **주요 기능:**
- 네이버 부동산 시세 자동 분석
- 투자금(갭) 실시간 계산
- 가격 변동 이메일 알림

✨ **베타 특전:**
- 완전 무료 사용
- 정식 출시 후에도 영구 무료
- 기능 요청 우선 반영

👉 **참여하기**: https://[your-app].streamlit.app

기간: 2026년 1월 ~ 2월
목표: 100명 베타 테스터
```

### 3. 피드백 수집

**GitHub Issues 템플릿:**
- Bug Report
- Feature Request
- Beta Feedback

---

## ⚠️ 알려진 제한사항

### SQLite 데이터 영속성
**문제:** Streamlit Cloud는 재배포 시 DB 초기화

**임시 해결책:**
- 베타 기간 동안 사용자가 데이터 재업로드
- 공지: "앱 업데이트 시 데이터 재업로드 필요"

**장기 해결책:**
- Supabase PostgreSQL 무료 티어로 마이그레이션

### 무료 플랜 제한
- 1GB RAM
- 1 CPU
- Private 앱 1개 (Public 무제한)

---

## 📞 도움말

**Streamlit 공식 문서:**
- 배포 가이드: https://docs.streamlit.io/deploy
- 커뮤니티: https://discuss.streamlit.io/

**프로젝트 문서:**
- `DEPLOYMENT.md` - 상세 배포 가이드
- `FAQ.md` - 자주 묻는 질문
- `EMAIL_SETUP.md` - 이메일 설정

---

## ✅ 성공 지표

**1주일:**
- 첫 10명 가입

**1개월:**
- 100명 가입
- 50명 활성 사용자
- 20건 피드백

**배포 완료 후 이 체크리스트를 따라 진행하세요!** 🚀
