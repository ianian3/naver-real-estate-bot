# .env 파일 생성 가이드

## 이메일 알림 설정 (Gmail)

1. **Gmail 앱 비밀번호 발급**
   - Google 계정 > 보안: https://myaccount.google.com/security
   - 2단계 인증 활성화 (필수)
   - 앱 비밀번호 생성 > "기타(맞춤 이름)" 선택 > "부동산알림"
   - 16자리 비밀번호 복사

2. **`.env` 파일 생성**
   ```bash
   # 프로젝트 루트에서
   cp .env.example .env
   ```

3. **환경변수 설정**
   `.env` 파일 편집:
   ```
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop  # 16자리 앱 비밀번호
   ```

4. **Streamlit 재시작**
   ```bash
   # Ctrl+C로 종료 후
   streamlit run app.py
   ```

## 테스트

1. Streamlit 사이드바에서 "🔔 알림 설정" 확인
2. "📧 테스트 이메일 발송" 버튼 클릭
3. 이메일 수신 확인

## 주의사항

- `.env` 파일은 `.gitignore`에 포함되어 자동으로 Git에서 제외됨
- 앱 비밀번호는 절대 공유하지 마세요
- Gmail 외 다른 SMTP 서버도 사용 가능 (src/notifications.py 수정)

## SendGrid 사용 (선택사항)

더 많은 이메일 발송이 필요한 경우:
1. SendGrid 계정 생성 (무료 티어: 월 100통)
2. API 키 발급
3. `.env`에 추가:
   ```
   SENDGRID_API_KEY=YOUR_API_KEY
   ```
4. `src/notifications.py` 수정
