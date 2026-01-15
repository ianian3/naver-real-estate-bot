"""
Celery 설정 파일
자동 크롤링 작업을 위한 백그라운드 작업 큐 설정
"""
from celery import Celery
from celery.schedules import crontab
import os

# Redis 연결 설정
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery 앱 초기화
app = Celery(
    'real_estate_crawler',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['worker.tasks']
)

# Celery 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분 타임아웃
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# Celery Beat 스케줄 (주기적 작업)
app.conf.beat_schedule = {
    'crawl-watchlist-daily': {
        'task': 'worker.tasks.crawl_all_watchlist',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
    },
}

if __name__ == '__main__':
    app.start()
