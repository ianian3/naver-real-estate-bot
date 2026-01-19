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
        
        # 가격 히스토리 테이블 (일별 요약)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complex_no TEXT NOT NULL,
                area_type TEXT NOT NULL,
                record_date DATE NOT NULL,
                
                -- 매매 통계
                sale_min_price BIGINT,
                sale_max_price BIGINT,
                sale_avg_price BIGINT,
                sale_count INTEGER DEFAULT 0,
                
                -- 전세 통계
                lease_min_price BIGINT,
                lease_max_price BIGINT,
                lease_avg_price BIGINT,
                lease_count INTEGER DEFAULT 0,
                
                -- 계산 지표
                gap_investment BIGINT,
                lease_ratio REAL,
                
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(complex_no, area_type, record_date),
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
        # price_history 인덱스
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_complex_no 
            ON price_history(complex_no)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_date 
            ON price_history(record_date)
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
        """
        매물 가격 정보를 데이터베이스에 저장
        
        주의: 가격은 \"만원\" 단위로 저장됨
        - 매매가: '가격' 컬럼에 저장 (원 단위 → 만원 단위로 변환)
        - 전세가: '보증금' 컬럼에 저장 (원 단위 → 만원 단위로 변환)
        """
        if df is None or df.empty:
            print(f"⚠ [{complex_no}] 저장할 매물 데이터가 없습니다.")
            return
        
        collected_at = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            # 가격을 원 단위 → 만원 단위로 변환
            price = row.get('가격', 0)
            deposit = row.get('보증금', 0)
            
            # 원 단위 검사 (100만 이상은 원 단위로 가정)
            if price > 1000000:
                price = int(price / 10000)  # 원 → 만원
            if deposit > 1000000:
                deposit = int(deposit / 10000)  # 원 → 만원
            
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
                price,  # 만원 단위
                row.get('거래유형', 'SALE'),
                deposit,  # 만원 단위
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
    
    def save_daily_summary(self, complex_no, record_date=None):
        """
        특정 단지의 당일 가격 데이터를 집계하여 price_history에 저장
        
        Args:
            complex_no: 단지 번호
            record_date: 기록 날짜 (기본값: 오늘)
        """
        if record_date is None:
            record_date = datetime.now().strftime('%Y-%m-%d')
        
        # 해당 날짜의 가격 데이터 집계
        query = '''
            SELECT 
                area_type,
                transaction_type,
                MIN(price) as min_price,
                MAX(price) as max_price,
                AVG(price) as avg_price,
                COUNT(*) as count
            FROM prices
            WHERE complex_no = ? AND DATE(collected_at) = ?
            GROUP BY area_type, transaction_type
        '''
        
        df = pd.read_sql_query(query, self.conn, params=[complex_no, record_date])
        
        if df.empty:
            print(f"⚠ [{complex_no}] {record_date}에 집계할 데이터가 없습니다.")
            return
        
        # 면적별로 집계
        area_types = df['area_type'].unique()
        
        for area_type in area_types:
            area_data = df[df['area_type'] == area_type]
            
            # 매매 데이터
            sale_data = area_data[area_data['transaction_type'] == 'SALE']
            sale_min = int(sale_data['min_price'].iloc[0]) if not sale_data.empty else None
            sale_max = int(sale_data['max_price'].iloc[0]) if not sale_data.empty else None
            sale_avg = int(sale_data['avg_price'].iloc[0]) if not sale_data.empty else None
            sale_count = int(sale_data['count'].iloc[0]) if not sale_data.empty else 0
            
            # 전세 데이터
            lease_data = area_data[area_data['transaction_type'] == 'LEASE']
            lease_min = int(lease_data['min_price'].iloc[0]) if not lease_data.empty else None
            lease_max = int(lease_data['max_price'].iloc[0]) if not lease_data.empty else None
            lease_avg = int(lease_data['avg_price'].iloc[0]) if not lease_data.empty else None
            lease_count = int(lease_data['count'].iloc[0]) if not lease_data.empty else 0
            
            # 갭 및 전세가율 계산
            gap_investment = None
            lease_ratio = None
            
            if sale_min and lease_max:
                gap_investment = sale_min - lease_max
            
            if sale_avg and lease_avg and sale_avg > 0:
                lease_ratio = round(lease_avg / sale_avg * 100, 1)
            
            # UPSERT (INSERT OR REPLACE)
            self.cursor.execute('''
                INSERT OR REPLACE INTO price_history 
                (complex_no, area_type, record_date, 
                 sale_min_price, sale_max_price, sale_avg_price, sale_count,
                 lease_min_price, lease_max_price, lease_avg_price, lease_count,
                 gap_investment, lease_ratio, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complex_no, area_type, record_date,
                sale_min, sale_max, sale_avg, sale_count,
                lease_min, lease_max, lease_avg, lease_count,
                gap_investment, lease_ratio,
                datetime.now().isoformat()
            ))
        
        self.conn.commit()
        print(f"✓ [{complex_no}] {record_date} 가격 히스토리 저장 완료 ({len(area_types)}개 면적)")
    
    def get_price_history(self, complex_no, area_type=None, days=90):
        """
        특정 단지의 가격 히스토리 조회
        
        Args:
            complex_no: 단지 번호
            area_type: 면적 타입 (선택)
            days: 조회할 일수 (기본 90일)
        
        Returns:
            DataFrame: 가격 히스토리
        """
        query = '''
            SELECT *
            FROM price_history
            WHERE complex_no = ?
              AND record_date >= DATE('now', ?)
        '''
        params = [complex_no, f'-{days} days']
        
        if area_type:
            query += ' AND area_type = ?'
            params.append(area_type)
        
        query += ' ORDER BY record_date ASC'
        
        return pd.read_sql_query(query, self.conn, params=params)
    
    def get_price_change(self, complex_no, area_type=None, compare_days=30):
        """
        가격 변동률 계산
        
        Args:
            complex_no: 단지 번호
            area_type: 면적 타입 (선택)
            compare_days: 비교 기간 (기본 30일)
        
        Returns:
            dict: 가격 변동 정보
        """
        history = self.get_price_history(complex_no, area_type, days=compare_days + 1)
        
        if history.empty or len(history) < 2:
            return None
        
        # 첫날과 마지막 날 비교
        first_day = history.iloc[0]
        last_day = history.iloc[-1]
        
        result = {
            'complex_no': complex_no,
            'area_type': area_type or 'ALL',
            'period_days': compare_days,
            'start_date': first_day['record_date'],
            'end_date': last_day['record_date']
        }
        
        # 매매가 변동
        if first_day['sale_avg_price'] and last_day['sale_avg_price']:
            sale_change = last_day['sale_avg_price'] - first_day['sale_avg_price']
            sale_change_pct = (sale_change / first_day['sale_avg_price']) * 100
            result['sale_current'] = last_day['sale_avg_price']
            result['sale_change'] = sale_change
            result['sale_change_pct'] = round(sale_change_pct, 2)
        
        # 전세가 변동
        if first_day['lease_avg_price'] and last_day['lease_avg_price']:
            lease_change = last_day['lease_avg_price'] - first_day['lease_avg_price']
            lease_change_pct = (lease_change / first_day['lease_avg_price']) * 100
            result['lease_current'] = last_day['lease_avg_price']
            result['lease_change'] = lease_change
            result['lease_change_pct'] = round(lease_change_pct, 2)
        
        # 갭 변동
        if first_day['gap_investment'] and last_day['gap_investment']:
            result['gap_current'] = last_day['gap_investment']
            result['gap_change'] = last_day['gap_investment'] - first_day['gap_investment']
        
        return result
    
    def get_area_types(self, complex_no):
        """특정 단지의 면적 타입 목록 조회"""
        query = '''
            SELECT DISTINCT area_type 
            FROM prices 
            WHERE complex_no = ? AND area_type != ''
            ORDER BY area_type
        '''
        df = pd.read_sql_query(query, self.conn, params=[complex_no])
        return df['area_type'].tolist()
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()
        print("✓ 데이터베이스 연결 종료")