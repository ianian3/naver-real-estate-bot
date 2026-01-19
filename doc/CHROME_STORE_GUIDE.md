# 🧩 Chrome Web Store 배포 가이드

## 📦 패키지 파일 위치
```
/Users/iankwon/naver_real_estage_bot/naver-real-estate-extension.zip
```

---

## 🚀 배포 단계

### Step 1: Chrome 개발자 계정 등록
1. https://chrome.google.com/webstore/devconsole 접속
2. Google 계정으로 로그인
3. **등록비 $5** 결제 (1회성)

### Step 2: 확장 프로그램 업로드
1. 개발자 대시보드에서 **"새 항목"** 클릭
2. `naver-real-estate-extension.zip` 업로드
3. 업로드 완료 대기

### Step 3: 스토어 등록 정보 입력

#### 기본 정보
| 항목 | 입력값 |
|------|--------|
| **이름** | 네이버 부동산 분석 도우미 |
| **요약** | 네이버 부동산 매물을 자동 분석하고 저환수원리 기준으로 투자 점수를 제공합니다 |
| **카테고리** | 생산성 또는 쇼핑 |

#### 상세 설명
```
🏢 네이버 부동산 분석 도우미

네이버 부동산에서 아파트 매물을 실시간으로 분석합니다.

✅ 주요 기능
• 면적별 최저가/최고가 자동 요약
• 🟢🟡🔴 신호등으로 저평가 매물 표시
• 갭(매매가-전세가) 자동 계산
• 전세가율 표시
• JSON 형식으로 데이터 내보내기

✅ 사용 방법
1. 네이버 부동산 (new.land.naver.com) 접속
2. 아파트 단지 선택
3. 매물 목록 페이지에서 자동 분석 시작!

✅ 연동 웹앱
수집한 데이터를 분석 앱에 업로드하면:
• 저환수원리 기준 투자 점수
• AI 투자 분석 보고서
• 가격 변동 추이 차트

📊 분석 앱: https://naver-real-estate-bot-jftvro8dufrp7z2yf7yh6j.streamlit.app

문의: GitHub Issues
```

### Step 4: 스크린샷 업로드
필요한 이미지:
1. **스크린샷 1-5장** (1280x800 권장)
2. **프로모션 타일** (440x280)
3. **마퀴 타일** (1400x560) - 선택

### Step 5: 개인정보처리방침
URL: https://ianian3.github.io/naver-real-estate-bot/privacy.html
(없으면 생성 필요)

### Step 6: 심사 제출
**"검토를 위해 제출"** 클릭

---

## ⏰ 심사 소요 시간
- 일반적으로 **1-3일**
- 최대 **7일**까지 소요될 수 있음

---

## ✅ 심사 통과 체크리스트
- [ ] manifest.json 버전 3 사용
- [ ] 필수 권한만 요청 (storage, activeTab)
- [ ] 아이콘 모든 사이즈 포함 (16, 48, 128)
- [ ] 개인정보처리방침 URL 제공
- [ ] 상세 설명에 기능 명확히 기재
