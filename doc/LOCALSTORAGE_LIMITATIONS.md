# LocalStorage 자동 업로드 제한사항

## 🚫 현재 문제

Streamlit은 브라우저의 LocalStorage를 **직접 읽을 수 없습니다**.

### 기술적 제한
- Streamlit은 Python 서버에서 실행
- LocalStorage는 브라우저(클라이언트)에만 존재
- JavaScript ↔ Python 직접 통신 불가

## ✅ 해결 방안

### 방법 1: JSON 파일 다운로드 (현재 권장) ⭐

**Tampermonkey:**
1. "💾 저장" - 여러 아파트 데이터 축적
2. "📥 전체 내보내기" - JSON 파일 다운로드

**Streamlit:**
3. "📥 데이터 가져오기" - JSON 파일 업로드

**장점:** 100% 작동, 안정적

### 방법 2: 클립보드 사용

**Tampermonkey 수정:**
```javascript
// 클립보드에 복사
function autoUploadToServer() {
    const data = localStorage.getItem('naver_real_estate_data');
    navigator.clipboard.writeText(data);
    alert('✅ 클립보드에 복사됨!\n\nStreamlit에서 붙여넣기하세요.');
}
```

**Streamlit:**
```python
uploaded_text = st.text_area("JSON 데이터 붙여넣기")
if st.button("업로드"):
    data = json.loads(uploaded_text)
```

### 방법 3: 파일 시스템 (로컬 전용)

**Tampermonkey:**
- 파일 쓰기 권한 없음 (보안상 불가능)

### 방법 4: 전용 Backend API (최상의 솔루션)

**구조:**
```
Tampermonkey → FastAPI → SQLite
                 ↓
            Streamlit
```

**장점:** 완전 자동화
**단점:** 별도 서버 필요

## 💡 현재 가장 실용적인 방법

### Streamlit Cloud Native 방식

**계속 JSON 파일 다운로드/업로드 사용**

```javascript
// Tampermonkey: 간소화
function quickExport() {
    const data = localStorage.getItem('naver_real_estate_data');
    const blob = new Blob([data], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'auto-export.json';
    a.click();
}
```

**사용자 경험:**
1. "자동 내보내기" 버튼 1번 클릭 → JSON 다운로드
2. Streamlit 파일 업로드 영역에 드래그&드롭

**소요 시간:** 5초

## 📊 비교

| 방법 | 자동화 | 안정성 | 구현 난이도 |
|------|--------|--------|------------|
| JSON 파일 | 수동 | ⭐⭐⭐⭐⭐ | 쉬움 |
| 클립보드 | 반자동 | ⭐⭐⭐ | 쉬움 |
| LocalStorage | X | ⭐ | 불가능 |
| Backend API | 완전자동 | ⭐⭐⭐⭐⭐ | 어려움 |

## 🎯 권장사항

**단기 (베타):**
- 계속 JSON 파일 방식 사용
- UI/UX 개선 (드래그&드롭)

**장기 (정식 출시):**
- FastAPI 백엔드 구축
- Chrome Extension 개발
