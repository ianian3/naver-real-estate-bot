import sqlite3
import pandas as pd
from datetime import datetime


class RealEstateDB:
    def __init__(self, db_path="data/real_estate.db"):
        """SQLite 데이터베이스 초기화"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        """데이터베이스 테이블 생성"""
        # 아파트 단지 정보 테이블
        # 기존 테이블 생성
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS complexes (
                complex_no TEXT PRIMARY KEY,
                complex_name TEXT,
                address TEXT,
                total_households INTEGER,
                build_year INTEGER,
                total_area REAL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complex_no TEXT,
                area_type TEXT,
                exclusive_area REAL,
                transaction_type TEXT,
                price BIGINT,
                deposit BIGINT,
                floor TEXT,
                floor_number INTEGER,
                direction TEXT,
                collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complex_no) REFERENCES complexes (complex_no)
            )
        ''')
        
        # 사용자 테이블 추가
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                max_watchlist INTEGER DEFAULT 3,
                email_notifications BOOLEAN DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 관심 단지 테이블
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                complex_no TEXT NOT NULL,
                complex_name TEXT,
                alert_price_drop REAL DEFAULT 5.0,
                alert_gap_threshold BIGINT DEFAULT 50000000,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, complex_no),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (complex_no) REFERENCES complexes (complex_no)
            )
        ''')
        
        # 인덱스 생성
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_complex_no 
            ON prices(complex_no)
        ''')
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_collected_at 
            ON prices(collected_at)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_floor_number 
            ON prices(floor_number)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_area_type 
            ON prices(area_type)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_prices_transaction_type 
            ON prices(transaction_type)
        ''')
        
        self.conn.commit()
        print(f"✓ 데이터베이스 테이블 초기화 완료: {self.db_path}")
    
    def save_complexes(self, df):
        """단지 정보를 데이터베이스에 저장 (UPSERT)"""
        if df is None or df.empty:
            print("⚠ 저장할 단지 데이터가 없습니다.")
            return
        
        updated_at = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            self.cursor.execute('''
                INSERT OR REPLACE INTO complexes 
                (complex_no, complex_name, address, total_households, build_year, total_area, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('단지번호', ''),
                row.get('단지명', ''),
                row.get('주소', ''),
                row.get('세대수', 0),
                row.get('건축년도', 2010),
                row.get('면적', 0.0),
                updated_at
            ))
        
        self.conn.commit()
        print(f"✓ {len(df)}개 단지 정보 저장 완료")
    
    def save_prices(self, df, complex_no):
        """매물 가격 정보를 데이터베이스에 저장"""
        if df is None or df.empty:
            print(f"⚠ [{complex_no}] 저장할 매물 데이터가 없습니다.")
            return
        
        collected_at = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            self.cursor.execute('''
                INSERT INTO prices 
                (complex_no, collected_at, area_type, exclusive_area, 
                 price, transaction_type, deposit, floor, floor_number, direction)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complex_no,
                collected_at,
                row.get('면적타입', ''),
                row.get('전용면적', 0.0),
                row.get('가격', 0),
                row.get('거래유형', 'SALE'),
                row.get('보증금', 0),
                row.get('층', ''),
                row.get('층수', 0),
                row.get('방향', '')
            ))
        
        self.conn.commit()
        print(f"✓ [{complex_no}] {len(df)}개 매물 정보 저장 완료")
    
    def get_all_complex_numbers(self):
        """관리 중인 모든 단지 번호 조회"""
        self.cursor.execute('SELECT complex_no FROM complexes')
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_price_trend(self, complex_no, area_type=None):
        """특정 단지의 가격 추이 조회 (Streamlit UI용)"""
        query = '''
            SELECT collected_at, area_type, AVG(price) as avg_price
            FROM prices
            WHERE complex_no = ?
        '''
        params = [complex_no]
        
        if area_type:
            query += ' AND area_type = ?'
            params.append(area_type)
        
        query += ' GROUP BY collected_at, area_type ORDER BY collected_at'
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_latest_prices(self, complex_no=None, limit=100):
        """최신 매물 정보 조회"""
        query = '''
            SELECT p.*, c.complex_name, c.address
            FROM prices p
            LEFT JOIN complexes c ON p.complex_no = c.complex_no
        '''
        params = []
        
        if complex_no:
            query += ' WHERE p.complex_no = ?'
            params.append(complex_no)
        
        query += ' ORDER BY p.collected_at DESC LIMIT ?'
        params.append(limit)
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_complex_info(self, complex_no):
        """특정 단지 정보 조회"""
        query = 'SELECT * FROM complexes WHERE complex_no = ?'
        result = pd.read_sql_query(query, self.conn, params=[complex_no])
        return result.iloc[0] if not result.empty else None
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()
        print("✓ 데이터베이스 연결 종료")