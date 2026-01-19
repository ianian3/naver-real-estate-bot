"""
Celery Worker 작업 정의
자동 크롤링 및 백그라운드 작업
"""
from celery_config import app
from src.database import RealEstateDB
from src.auth import UserManager
from src.notifications import EmailNotifier
from src.analyzer import get_price_summary_by_area
import json
import logging
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

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
        from src.crawler import get_listings_api
        
        db = RealEstateDB()
        
        # 매매 데이터 수집
        sale_df = get_listings_api(complex_no, 'SALE')
        if not sale_df.empty:
            db.save_prices(sale_df, complex_no)
            logger.info(f"✓ {complex_name} 매매 {len(sale_df)}개 저장")
        
        # 전세 데이터 수집
        lease_df = get_listings_api(complex_no, 'LEASE')
        if not lease_df.empty:
            db.save_prices(lease_df, complex_no)
            logger.info(f"✓ {complex_name} 전세 {len(lease_df)}개 저장")
        
        logger.info(f"Crawl completed for {complex_name}")
        
        return {
            'status': 'success',
            'complex_no': complex_no,
            'complex_name': complex_name,
            'sale_count': len(sale_df),
            'lease_count': len(lease_df)
        }
    
    except Exception as e:
        logger.error(f"Error crawling {complex_name}: {str(e)}")
        return {
            'status': 'error',
            'complex_no': complex_no,
            'complex_name': complex_name,
            'error': str(e)
        }


@app.task(name='worker.tasks.check_price_changes')
def check_price_changes(user_id: int, complex_no: str, complex_name: str, area_type: str = None):
    """
    가격 변동 감지 및 알림 발송
    
    Args:
        user_id: 사용자 ID
        complex_no: 단지 번호
        complex_name: 단지명
        area_type: 면적 타입 (예: '59A', '84A')
    
    Returns:
        dict: 결과
    """
    logger.info(f"Checking price changes for {complex_name} (user: {user_id})")
    
    try:
        db = RealEstateDB()
        user_manager = UserManager()
        notifier = EmailNotifier()
        
        # 사용자 정보 조회
        user = user_manager.get_user_by_username(str(user_id))
        if not user:
            logger.warning(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}
        
        user_email = user.get('email')
        if not user_email:
            return {'status': 'error', 'message': 'No email found'}
        
        # 최근 2개의 데이터 조회 (현재 + 이전)
        query = """
            SELECT collected_at, area_type, price, transaction_type
            FROM prices
            WHERE complex_no = ? AND transaction_type = 'SALE'
            ORDER BY collected_at DESC
            LIMIT 2
        """
        
        conn = sqlite3.connect('data/real_estate.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (complex_no,))
        results = cursor.fetchall()
        conn.close()
        
        if len(results) < 2:
            logger.info(f"Not enough data for {complex_no}")
            return {'status': 'success', 'message': 'Not enough historical data'}
        
        current = dict(results[0])
        previous = dict(results[1])
        
        # 가격 변동 계산
        current_price = current['price'] / 100000000  # 원 → 억
        previous_price = previous['price'] / 100000000
        price_change = current_price - previous_price
        price_change_percent = (price_change / previous_price * 100) if previous_price > 0 else 0
        
        logger.info(f"Price change: {previous_price:.1f}억 → {current_price:.1f}억 ({price_change_percent:+.1f}%)")
        
        # 5% 이상 변동 시 알림
        if abs(price_change_percent) >= 5:
            subject = f"📊 {complex_name} 가격 변동 알림"
            
            if price_change_percent < 0:
                # 하락 알림
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4CAF50;">✅ 좋은 기회! 가격 하락</h2>
                        <p><strong>{complex_name}</strong></p>
                        <p>이전 가격: <strong>{previous_price:.1f}억</strong></p>
                        <p>현재 가격: <strong style="color: #4CAF50;">{current_price:.1f}억</strong></p>
                        <p>변동: <strong style="color: #4CAF50;">{price_change:+.1f}억 ({price_change_percent:.1f}%)</strong></p>
                    </div>
                </body>
                </html>
                """
            else:
                # 상승 알림
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #E53935;">📈 주의! 가격 상승</h2>
                        <p><strong>{complex_name}</strong></p>
                        <p>이전 가격: <strong>{previous_price:.1f}억</strong></p>
                        <p>현재 가격: <strong style="color: #E53935;">{current_price:.1f}억</strong></p>
                        <p>변동: <strong style="color: #E53935;">{price_change:+.1f}억 ({price_change_percent:.1f}%)</strong></p>
                    </div>
                </body>
                </html>
                """
            
            notifier.send_email(user_email, subject, html_content)
            logger.info(f"Alert sent to {user_email}")
        
        return {
            'status': 'success',
            'complex_no': complex_no,
            'complex_name': complex_name,
            'price_change_percent': price_change_percent,
            'alert_sent': abs(price_change_percent) >= 5
        }
    
    except Exception as e:
        logger.error(f"Error checking price changes: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@app.task(name='worker.tasks.crawl_all_watchlist')
def crawl_all_watchlist():
    """
    모든 사용자의 관심 단지를 크롤링 및 알림 발송
    매일 자동으로 실행됨 (Celery Beat)
    
    Returns:
        dict: 크롤링 결과 요약
    """
    logger.info("Starting daily watchlist crawl")
    
    try:
        # 모든 사용자의 관심 단지 가져오기
        query = """
            SELECT DISTINCT w.user_id, w.complex_no, w.complex_name, COUNT(w.user_id) as user_count
            FROM watchlist w
            GROUP BY w.user_id, w.complex_no
        """
        
        conn = sqlite3.connect('data/real_estate.db')
        cursor = conn.cursor()
        cursor.execute(query)
        watchlist_items = cursor.fetchall()
        conn.close()
        
        results = []
        crawl_tasks = []
        check_tasks = []
        
        for user_id, complex_no, complex_name, user_count in watchlist_items:
            # 각 단지에 대해 크롤링 작업 실행
            crawl_result = crawl_complex.delay(complex_no, complex_name)
            crawl_tasks.append(crawl_result)
            
            # 가격 변동 확인 작업 실행
            check_result = check_price_changes.delay(user_id, complex_no, complex_name)
            check_tasks.append(check_result)
            
            results.append({
                'user_id': user_id,
                'complex_no': complex_no,
                'complex_name': complex_name,
                'user_count': user_count,
                'crawl_task_id': crawl_result.id,
                'check_task_id': check_result.id
            })
        
        logger.info(f"Queued {len(results)} crawl and check tasks")
        
        return {
            'status': 'success',
            'total_complexes': len(results),
            'crawl_tasks': len(crawl_tasks),
            'check_tasks': len(check_tasks),
            'results': results
        }
    
    except Exception as e:
        logger.error(f"Error in crawl_all_watchlist: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@app.task(name='worker.tasks.cleanup_old_prices')
def cleanup_old_prices(days: int = 90):
    """
    90일 이상 된 가격 데이터 정리
    스토리지 공간 절약용
    
    Args:
        days: 지난 일수 (기본 90일)
    
    Returns:
        dict: 정리 결과
    """
    logger.info(f"Cleaning up prices older than {days} days")
    
    try:
        db = RealEstateDB()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = "DELETE FROM prices WHERE collected_at < ?"
        db.cursor.execute(query, (cutoff_date,))
        db.conn.commit()
        
        deleted_count = db.cursor.rowcount
        logger.info(f"Deleted {deleted_count} old price records")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up prices: {str(e)}")
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

