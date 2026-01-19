# Week 2: 자동 크롤링 시스템 설정 가이드

## 🚀 Redis 설치 및 실행

### macOS (Homebrew)
```bash
# Redis 설치
brew install redis

# Redis 서버 시작 (백그라운드)
brew services start redis

# 또는 포그라운드 실행
redis-server
```

### 확인
```bash
# Redis 연결 테스트
redis-cli ping
# 응답: PONG
```

## 🔧 Celery Worker 실행

### 1. Celery Worker 시작
```bash
cd /Users/iankwon/naver_real_estage_bot
source venv/bin/activate
celery -A celery_config worker --loglevel=info
```

### 2. Celery Beat 시작 (스케줄러)
**새 터미널에서:**
```bash
cd /Users/iankwon/naver_real_estage_bot
source venv/bin/activate
celery -A celery_config beat --loglevel=info
```

## 🧪 테스트

### 1. 간단한 작업 테스트
```python
from worker.tasks import test_task

# 작업 실행
result = test_task.delay("Hello Celery!")

# 결과 확인
print(result.get(timeout=10))
```

### 2. 크롤링 작업 테스트
```python
from worker.tasks import crawl_complex

# 단일 단지 크롤링
result = crawl_complex.delay("12345", "테스트아파트")
print(result.get(timeout=30))
```

### 3. 전체 관심 단지 크롤링
```python
from worker.tasks import crawl_all_watchlist

# 모든 관심 단지 크롤링
result = crawl_all_watchlist.delay()
print(result.get(timeout=60))
```

## 📊 Celery Flower (모니터링, 선택사항)

```bash
# Flower 설치
pip install flower

# Flower 실행
celery -A celery_config flower
# 접속: http://localhost:5555
```

## 🔄 자동 실행 스케줄

**현재 설정:**
- **매일 새벽 2시**: 모든 관심 단지 자동 크롤링

**변경 방법:**
`celery_config.py`의 `beat_schedule` 수정

```python
app.conf.beat_schedule = {
    'crawl-watchlist-daily': {
        'task': 'worker.tasks.crawl_all_watchlist',
        'schedule': crontab(hour=2, minute=0),  # 시간 변경
    },
}
```

## ⚠️ 주의사항

1. **Redis 실행 필수**: Celery Worker 실행 전 Redis 서버가 실행 중이어야 함
2. **3개 프로세스 필요**:
   - Streamlit 앱
   - Celery Worker
   - Celery Beat (스케줄러)
3. **포트**: Redis는 기본적으로 6379 포트 사용

## 📝 다음 단계

- [ ] 실제 크롤링 로직 구현 (`worker/tasks.py`)
- [ ] UI에 크롤링 상태 표시
- [ ] 에러 재시도 로직 추가
