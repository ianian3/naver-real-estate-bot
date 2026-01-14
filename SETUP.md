# 🚀 다른 컴퓨터에서 개발 이어하기

## 방법 1: Git/GitHub 사용 (추천 ⭐)

### 1️⃣ 현재 컴퓨터에서 GitHub에 업로드

```bash
cd /Users/iankwon/naver_real_estage_bot

# Git 초기화 (처음만)
git init

# 파일 추가
git add .

# 커밋
git commit -m "Initial commit: Naver Real Estate Bot with Streamlit UI"

# GitHub 저장소 연결 (본인의 GitHub 저장소 URL로 변경)
git remote add origin https://github.com/ianian3/naver_real_estate_bot.git

# 업로드
git push -u origin main
```

### 2️⃣ 다른 컴퓨터에서 다운로드

```bash
# 저장소 복제
git clone https://github.com/ianian3/naver_real_estate_bot.git
cd naver_real_estate_bot

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Streamlit 실행
streamlit run app.py
```

### 3️⃣ 수정사항 동기화

**현재 컴퓨터에서 푸시:**
```bash
git add .
git commit -m "작업 내용 설명"
git push
```

**다른 컴퓨터에서 풀:**
```bash
git pull
```

---

## 방법 2: 압축 파일 백업

### 백업 생성
```bash
cd /Users/iankwon
tar -czf naver_real_estage_bot_backup.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.db' \
  naver_real_estage_bot/
```

### 복원
```bash
# 압축 해제
tar -xzf naver_real_estage_bot_backup.tar.gz
cd naver_real_estage_bot

# 환경 재설정
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 방법 3: 클라우드 드라이브 (Google Drive, iCloud 등)

1. 프로젝트 폴더를 클라우드 드라이브로 이동
2. 다른 컴퓨터에서 동기화
3. **주의:** `venv/`, `__pycache__/`, `*.db` 파일은 동기화 제외 권장

---

## 📝 중요 파일 목록

### 반드시 포함할 파일:
- ✅ `app.py` - Streamlit UI
- ✅ `main.py` - 메인 실행 파일
- ✅ `requirements.txt` - 패키지 목록
- ✅ `tampermonkey_export.js` - Tampermonkey 스크립트
- ✅ `src/*.py` - 모든 Python 모듈
- ✅ `README.md`, `IMPORT_GUIDE.md` - 문서

### 제외해도 되는 파일:
- ❌ `venv/` - 가상환경 (다른 컴퓨터에서 재생성)
- ❌ `__pycache__/` - Python 캐시
- ❌ `*.db` - 데이터베이스 (선택사항)
- ❌ `.DS_Store` - macOS 시스템 파일

---

## 🎯 추천 방법

**Git/GitHub** 사용을 강력히 추천합니다:
- ✅ 버전 관리 가능
- ✅ 변경 이력 추적
- ✅ 협업 용이
- ✅ 무료
- ✅ 언제 어디서나 접근 가능
