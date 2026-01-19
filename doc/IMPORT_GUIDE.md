# 실제 네이버 데이터 수집 가이드

Tampermonkey 스크립트를 통해 실제 네이버 부동산 데이터를 수집하는 방법입니다.

## 1단계: Tampermonkey 스크립트 수정

### 기존 스크립트에 추가할 코드

기존 Tampermonkey 스크립트 **맨 아래**에 `tampermonkey_export.js` 파일의 내용을 추가하세요.

또는 새로운 스크립트를 생성해도 됩니다.

### 주요 기능

- **"📥 Python으로 내보내기"** 버튼이 오른쪽 상단에 나타남
- 클릭하면 현재 보고 있는 단지의 데이터를 JSON으로 다운로드
- 월부 기준 필터링이 적용된 데이터 수집

---

## 2단계: 네이버 부동산에서 데이터 수집

1. **네이버 부동산 접속**
   ```
   https://new.land.naver.com
   ```

2. **원하는 지역 검색** (예: 강남구)

3. **아파트 단지 클릭**
   - 예: 래미안대치팰리스
   - 예: 아크로리버파크

4. **매물 리스트가 로드될 때까지 대기**
   - 무한 스크롤로 매물 모두 로드

5. **"📥 Python으로 내보내기" 버튼 클릭**
   - JSON 파일 자동 다운로드
   - 파일명: `naver_래미안대치팰리스_1234567890.json`

6. **다운로드한 JSON 파일을 `data/exports/` 폴더로 이동**

---

## 3단계: Python으로 데이터 가져오기

### 단일 파일 가져오기

```bash
python import_json.py data/exports/naver_래미안대치팰리스_1234567890.json
```

### 폴더 내 모든 파일 가져오기

```bash
python import_json.py data/exports/
```

---

## 4단계: Streamlit에서 확인

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 접속하여 데이터 확인!

---

## JSON 파일 구조

```json
{
  "metadata": {
    "complex_no": "12957",
    "complex_name": "래미안대치팰리스",
    "address": "서울 강남구 대치동",
    "collected_at": "2026-01-13T10:00:00.000Z",
    "collector": "tampermonkey_script"
  },
  "listings": [
    {
      "area_type": "103/84m²",
      "exclusive_area": 84,
      "sale_price": 170000,
      "sale_floor": "10",
      "sale_count": 5,
      "lease_price": 130000,
      "lease_floor": "12",
      "lease_count": 3,
      "gap": 40000,
      "lease_rate": "76%"
    }
  ]
}
```

---

## 주의사항

### 필터링 적용

import_json.py는 자동으로 다음 필터링을 적용합니다:

- ✅ **4층 이상만**
- ✅ **59m² 또는 84m²만** (±3m²)
- ✅ **매매/전세 구분**

### 데이터 중복

- 같은 단지를 여러 번 가져오면 **덮어쓰기** 됩니다
- 가장 최근에 가져온 데이터가 유지됩니다

---

## 팁

### 여러 단지 한번에 수집

1. 네이버 부동산에서 단지 1 클릭 → 내보내기
2. 단지 2 클릭 → 내보내기
3. 단지 3 클릭 → 내보내기
4. ...
5. `python import_json.py data/exports/` 한 번에 가져오기

### 데이터 백업

```bash
cp data/real_estate.db data/real_estate_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 문제 해결

### "파일을 찾을 수 없습니다"

→ JSON 파일이 `data/exports/` 폴더에 있는지 확인

### "JSON 파싱 오류"

→ JSON 파일이 손상되었을 수 있음. 브라우저에서 다시 내보내기

### "매물 데이터가 없습니다"

→ 네이버에서 매물 리스트를 충분히 스크롤한 후 내보내기
