#!/usr/bin/env python3
import sqlite3
import os

db_path = 'data/real_estate.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. complexes 테이블 데이터 확인
    print("=== COMPLEXES 테이블 ===")
    cursor.execute("SELECT COUNT(*) FROM complexes")
    count = cursor.fetchone()[0]
    print(f"단지 개수: {count}")
    
    if count > 0:
        cursor.execute("SELECT complex_no, complex_name FROM complexes")
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1]}")
    
    # 2. prices 테이블 데이터 확인
    print("\n=== PRICES 테이블 ===")
    cursor.execute("SELECT COUNT(*) FROM prices")
    count = cursor.fetchone()[0]
    print(f"매물 개수: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT 
                c.complex_name,
                p.area_type,
                p.transaction_type,
                p.price,
                p.deposit
            FROM prices p
            JOIN complexes c ON p.complex_no = c.complex_no
            LIMIT 20
        """)
        for row in cursor.fetchall():
            print(f"  {row}")
    
    conn.close()
else:
    print("❌ 데이터베이스 파일 없음")
