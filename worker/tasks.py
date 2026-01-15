"""
Celery Worker 작업 정의
자동 크롤링 및 백그라운드 작업
"""
from celery_config import app
from src.database import RealEstateDB
from src.auth import UserManager
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.task(name='worker.tasks.crawl_complex')
def crawl_complex(complex_no: str, complex_name: str):
    """
    특정 단지의 데이터를 크롤링
    
    Args:
        complex_no: 단지 번호
        complex_name: 단지명
    
    Returns:
        dict: 크롤링 결과
    """
    logger.info(f"Starting crawl for {complex_name} ({complex_no})")
    
    try:
        # TODO: 실제 크롤링 로직 구현
        # 현재는 테스트용 더미 데이터
        
        logger.info(f"Crawl completed for {complex_name}")
        return {
            'status': 'success',
            'complex_no': complex_no,
            'complex_name': complex_name,
            'message': 'Crawling completed (dummy data)'
        }
    
    except Exception as e:
        logger.error(f"Error crawling {complex_name}: {str(e)}")
        return {
            'status': 'error',
            'complex_no': complex_no,
            'complex_name': complex_name,
            'error': str(e)
        }


@app.task(name='worker.tasks.crawl_all_watchlist')
def crawl_all_watchlist():
    """
    모든 사용자의 관심 단지를 크롤링
    매일 자동으로 실행됨 (Celery Beat)
    
    Returns:
        dict: 크롤링 결과 요약
    """
    logger.info("Starting daily watchlist crawl")
    
    try:
        db = RealEstateDB()
        user_manager = UserManager()
        
        # 모든 사용자의 관심 단지 가져오기
        query = """
            SELECT DISTINCT w.complex_no, w.complex_name, COUNT(w.user_id) as user_count
            FROM watchlist w
            GROUP BY w.complex_no
        """
        
        import sqlite3
        conn = sqlite3.connect('data/real_estate.db')
        cursor = conn.cursor()
        cursor.execute(query)
        watchlist_items = cursor.fetchall()
        conn.close()
        
        results = []
        for complex_no, complex_name, user_count in watchlist_items:
            # 각 단지에 대해 비동기 크롤링 작업 실행
            result = crawl_complex.delay(complex_no, complex_name)
            results.append({
                'complex_no': complex_no,
                'complex_name': complex_name,
                'user_count': user_count,
                'task_id': result.id
            })
        
        logger.info(f"Queued {len(results)} crawl tasks")
        
        return {
            'status': 'success',
            'total_complexes': len(results),
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Error in crawl_all_watchlist: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@app.task(name='worker.tasks.test_task')
def test_task(message: str):
    """
    테스트용 간단한 작업
    
    Args:
        message: 테스트 메시지
    
    Returns:
        str: 결과 메시지
    """
    logger.info(f"Test task received: {message}")
    return f"Task completed: {message}"
