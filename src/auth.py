"""
사용자 인증 관리 모듈
"""
import sqlite3
import bcrypt
from typing import Optional, Dict, List


class UserManager:
    """사용자 인증 및 관리"""
    
    def __init__(self, db_path: str = "data/real_estate.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """DB 연결"""
        return sqlite3.connect(self.db_path)
    
    def create_user(self, username: str, email: str, password: str) -> bool:
        """새 사용자 생성"""
        try:
            # 비밀번호 해싱
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """사용자 인증"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, password_hash, plan, max_watchlist
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'plan': user[4],
                'max_watchlist': user[5]
            }
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """사용자 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, email, plan, max_watchlist
            FROM users WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'plan': user[3],
                'max_watchlist': user[4]
            }
        return None
    
    def add_to_watchlist(self, user_id: int, complex_no: str, complex_name: str) -> bool:
        """관심 단지 추가"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO watchlist (user_id, complex_no, complex_name)
                VALUES (?, ?, ?)
            ''', (user_id, complex_no, complex_name))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_from_watchlist(self, user_id: int, complex_no: str) -> bool:
        """관심 단지 제거"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM watchlist WHERE user_id = ? AND complex_no = ?
        ''', (user_id, complex_no))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_watchlist(self, user_id: int) -> List[Dict]:
        """사용자 관심 단지 목록"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT complex_no, complex_name, alert_price_drop, alert_gap_threshold, created_at
            FROM watchlist WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        watchlist = cursor.fetchall()
        conn.close()
        
        return [{
            'complex_no': w[0],
            'complex_name': w[1],
            'alert_price_drop': w[2],
            'alert_gap_threshold': w[3],
            'created_at': w[4]
        } for w in watchlist]
    
    def get_watchlist_count(self, user_id: int) -> int:
        """관심 단지 개수"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM watchlist WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def can_add_watchlist(self, user_id: int) -> bool:
        """관심 단지 추가 가능 여부 확인"""
        user = self.get_user_by_username(username='')  # 실제로는 user_id로 조회
        if not user:
            return False
        
        current_count = self.get_watchlist_count(user_id)
        return current_count < user['max_watchlist']
