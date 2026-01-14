import streamlit as st
from src.database import RealEstateDB
from src.analyzer import get_all_area_summaries, format_price_display
import plotly.express as px
import pandas as pd
from datetime import datetime
import json
import tempfile
import os
import subprocess
import time

# 페이지 설정
st.set_page_config(
    page_title="부동산 데이터 분석",
    page_icon="🏢",
    layout="wide"
)

# 타이틀
st.title("🏢 네이버 부동산 가격 분석")

# DB 연결 (파일 업로드 전에 먼저 정의)
@st.cache_resource
def get_db():
    return RealEstateDB("data/real_estate.db")

db = get_db()

# 사이드바 - 파일 업로드 기능
st.sidebar.header("📥 데이터 가져오기")

uploaded_file = st.sidebar.file_uploader(
    "JSON 파일 업로드",
    type=['json'],
    help="Tampermonkey에서 내보낸 JSON 파일을 업로드하세요"
)

if uploaded_file is not None:
    try:
        # JSON 파일 읽기
        json_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
        
        # 메타데이터 추출
        metadata = json_data.get('metadata', {})
        complex_name = metadata.get('complex_name', 'Unknown')
        complex_no = metadata.get('complex_no', 'unknown')
        total_households = metadata.get('total_households', 0)
        
        # 기존 데이터 삭제 (중복 방지)
        db.conn.execute("DELETE FROM prices WHERE complex_no = ?", (complex_no,))
        db.conn.commit()
        
        # DB에 단지 정보 저장 (UPDATE 또는 INSERT)
        db.conn.execute("""
            INSERT OR REPLACE INTO complexes (complex_no, complex_name, address, total_households, build_year, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (complex_no, complex_name, metadata.get('address', ''), total_households, 2010))
        db.conn.commit()
        
        # 매물 데이터 처리
        listings = json_data.get('listings', [])
        sale_count = 0
        lease_count = 0
        
        for listing in listings:
            area = listing.get('exclusive_area', 0)
            area_type = listing.get('area_type', '')  # 원본 타입명 사용 (예: 86B/59m², 111A/84m²)
            
            # 면적 필터링 (59m², 75m², 84m²)
            if not (56 <= area <= 62 or 72 <= area <= 78 or 81 <= area <= 87):
                continue
            
            # 매매 데이터
            if listing.get('sale_price', 0) > 0 and listing.get('sale_count', 0) > 0:
                floor_str = listing.get('sale_floor', '')
                floor_num = 15 if '고' in floor_str else 9 if '중' in floor_str else 5 if floor_str.isdigit() else 5
                
                if floor_num >= 4:
                    sale_df = pd.DataFrame([{
                        '면적타입': area_type,
                        '전용면적': area,
                        '거래유형': 'SALE',
                        '층': floor_str,
                        '층수': floor_num,
                        '방향': '',
                        '가격': listing.get('sale_price', 0) * 10000,
                        '보증금': 0,
                    }])
                    db.save_prices(sale_df, complex_no)
                    sale_count += 1
            
            # 전세 데이터
            if listing.get('lease_price', 0) > 0 and listing.get('lease_count', 0) > 0:
                floor_str = listing.get('lease_floor', '')
                floor_num = 15 if '고' in floor_str else 9 if '중' in floor_str else 5 if floor_str.isdigit() else 5
                
                if floor_num >= 4:
                    lease_df = pd.DataFrame([{
                        '면적타입': area_type,
                        '전용면적': area,
                        '거래유형': 'LEASE',
                        '층': floor_str,
                        '층수': floor_num,
                        '방향': '',
                        '가격': 0,
                        '보증금': listing.get('lease_price', 0) * 10000,
                    }])
                    db.save_prices(lease_df, complex_no)
                    lease_count += 1
        
        st.sidebar.success(f"✅ {complex_name} 가져오기 성공!")
        st.sidebar.info(f"매매 {sale_count}개, 전세 {lease_count}개")
        
        # 캐시 클리어하여 데이터 새로고침
        st.cache_data.clear()
        st.success("데이터가 업데이트되었습니다! 잠시 후 자동으로 새로고침됩니다...")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.sidebar.error(f"❌ 오류: {str(e)}")

st.sidebar.divider()

# 사이드바 필터
st.sidebar.header("🔍 필터")

# 데이터 로드 함수
@st.cache_data(ttl=60)
def load_formatted_data():
    try:
        query = """
        SELECT 
            c.complex_name as 아파트명,
            c.total_households as 세대수,
            c.build_year as 건축년도,
            (2026 - c.build_year) as 연식,
            p.area_type as 타입,
            p.exclusive_area as 면적_m2,
            CASE 
                WHEN p.transaction_type = 'SALE' THEN ROUND(p.price / 100000000.0, 2)
                ELSE 0
            END as 매매가_억,
            CASE 
                WHEN p.transaction_type = 'LEASE' THEN ROUND(p.deposit / 100000000.0, 2)
                ELSE 0
            END as 전세가_억,
            p.transaction_type,
            p.floor,
            p.floor_number as 층수,
            p.direction as 방향,
            p.collected_at
        FROM prices p
        JOIN complexes c ON p.complex_no = c.complex_no
        ORDER BY c.complex_name, p.area_type, p.transaction_type
        """
        return pd.read_sql_query(query, db.conn)
    except Exception as e:
        # DB가 비어있거나 오류 발생 시 빈 DataFrame 반환
        return pd.DataFrame()

df = load_formatted_data()

# 데이터가 없는 경우 처리
if df.empty:
    st.info("📊 데이터가 없습니다. 좌측 사이드바에서 JSON 파일을 업로드하세요.")
    st.stop()

# 필터 옵션
selected_type = st.sidebar.selectbox(
    "거래유형",
    ["전체", "매매만", "전세만"]
)

selected_area = st.sidebar.selectbox(
    "면적",
    ["전체", "59m²", "75m²", "84m²"]
)

st.sidebar.divider()
st.sidebar.subheader("🛠️ 필터 옵션")

# 필터 옵션 설명
exclude_seango = st.sidebar.checkbox(
    "✅ 세안고/끼고 제외",
    value=True,
    help="세입자끼고, 전세안고 매물 제외"
)

exclude_low_floors = st.sidebar.checkbox(
    "✅ 저층/탑층 제외",
    value=True,
    help="1-3층, 탑층 매물 제외 (매매만)"
)

signal_multiplier = st.sidebar.radio(
    "🚦 신호등 배율",
    options=[1, 2, 3],
    format_func=lambda x: f"X{x}",
    index=0,
    help=f"가격 차이 기준:\n- 녹색: {5}% 미만\n- 주황: {10}% 미만\n- 빨강: {10}% 이상"
)

st.sidebar.caption("ℹ️ 필터는 새 데이터 수집 시 적용됩니다")

# 필터링 적용
filtered_df = df.copy()

if selected_type == "매매만":
    filtered_df = filtered_df[filtered_df['transaction_type'] == 'SALE']
elif selected_type == "전세만":
    filtered_df = filtered_df[filtered_df['transaction_type'] == 'LEASE']

if selected_area != "전체":
    if "59" in selected_area:
        filtered_df = filtered_df[(filtered_df['면적_m2'] >= 56) & (filtered_df['면적_m2'] <= 62)]
    elif "75" in selected_area:
        filtered_df = filtered_df[(filtered_df['면적_m2'] >= 72) & (filtered_df['면적_m2'] <= 78)]
    elif "84" in selected_area:
        filtered_df = filtered_df[(filtered_df['면적_m2'] >= 81) & (filtered_df['면적_m2'] <= 87)]

# 통계 카드
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("총 매물 수", f"{len(filtered_df):,}개")

with col2:
    sale_count = len(filtered_df[filtered_df['transaction_type'] == 'SALE'])
    st.metric("매매", f"{sale_count:,}개")

with col3:
    lease_count = len(filtered_df[filtered_df['transaction_type'] == 'LEASE'])
    st.metric("전세", f"{lease_count:,}개")

with col4:
    complex_count = filtered_df['아파트명'].nunique()
    st.metric("단지 수", f"{complex_count}개")

st.divider()

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["📋 매물 리스트", "📊 가격 분석", "🏢 아파트별 통계", "💾 내보내기"])

with tab1:
    st.subheader("📋 매물 목록 (사용자 요청 컬럼)")
    
    # 거래유형 표시
    display_df = filtered_df.copy()
    display_df['거래유형'] = display_df['transaction_type'].map({'SALE': '매매', 'LEASE': '전세'})
    
    # 사용자가 요청한 컬럼 순서대로 표시
    display_cols = ['아파트명', '세대수', '연식', '면적_m2', '매매가_억', '전세가_억', '타입', '층수', 'floor', '방향']
    col_names = ['아파트명', '세대수', '연식(년)', '면적(m²)', '매매가(억)', '전세가(억)', '타입', '층수', '층표시', '방향']
    
    show_df = display_df[display_cols].copy()
    show_df.columns = col_names
    
    # 데이터 타입 포맷팅
    show_df['매매가(억)'] = show_df['매매가(억)'].apply(lambda x: f"{x:.1f}" if x > 0 else "-")
    show_df['전세가(억)'] = show_df['전세가(억)'].apply(lambda x: f"{x:.1f}" if x > 0 else "-")
    
    st.dataframe(
        show_df,
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    st.caption(f"총 {len(show_df):,}개 매물")

with tab2:
    st.subheader("📊 면적별 가격 분석")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### 매매가")
        sale_df = filtered_df[filtered_df['매매가_억'] > 0].copy()
        if not sale_df.empty:
            sale_stats = sale_df.groupby('면적_m2').agg({
                '매매가_억': ['count', 'mean', 'min', 'max']
            }).round(1)
            sale_stats.columns = ['매물수', '평균(억)', '최저(억)', '최고(억)']
            st.dataframe(sale_stats, use_container_width=True)
            
            # 아파트별 평균 가격 계산
            sale_avg = sale_df.groupby(['아파트명', '면적_m2'])['매매가_억'].mean().reset_index()
            sale_avg.columns = ['아파트명', '면적(m²)', '평균가격(억)']
            
            # 59m² 차트
            sale_59 = sale_avg[(sale_avg['면적(m²)'] >= 56) & (sale_avg['면적(m²)'] <= 62)]
            if not sale_59.empty:
                fig1_59 = px.bar(
                    sale_59,
                    x='아파트명',
                    y='평균가격(억)',
                    title='59m² 아파트별 평균 매매가',
                    labels={'평균가격(억)': '평균 매매가 (억원)', '아파트명': '아파트'},
                    color='평균가격(억)',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig1_59, use_container_width=True)
            
            # 84m² 차트
            sale_84 = sale_avg[(sale_avg['면적(m²)'] >= 81) & (sale_avg['면적(m²)'] <= 87)]
            if not sale_84.empty:
                fig1_84 = px.bar(
                    sale_84,
                    x='아파트명',
                    y='평균가격(억)',
                    title='84m² 아파트별 평균 매매가',
                    labels={'평균가격(억)': '평균 매매가 (억원)', '아파트명': '아파트'},
                    color='평균가격(억)',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig1_84, use_container_width=True)
        else:
            st.info("매매 데이터가 없습니다.")
    
    with col2:
        st.markdown("##### 전세가")
        lease_df = filtered_df[filtered_df['전세가_억'] > 0].copy()
        if not lease_df.empty:
            lease_stats = lease_df.groupby('면적_m2').agg({
                '전세가_억': ['count', 'mean', 'min', 'max']
            }).round(1)
            lease_stats.columns = ['매물수', '평균(억)', '최저(억)', '최고(억)']
            st.dataframe(lease_stats, use_container_width=True)
            
            # 아파트별 평균 가격 계산
            lease_avg = lease_df.groupby(['아파트명', '면적_m2'])['전세가_억'].mean().reset_index()
            lease_avg.columns = ['아파트명', '면적(m²)', '평균가격(억)']
            
            # 59m² 차트
            lease_59 = lease_avg[(lease_avg['면적(m²)'] >= 56) & (lease_avg['면적(m²)'] <= 62)]
            if not lease_59.empty:
                fig2_59 = px.bar(
                    lease_59,
                    x='아파트명',
                    y='평균가격(억)',
                    title='59m² 아파트별 평균 전세가',
                    labels={'평균가격(억)': '평균 전세가 (억원)', '아파트명': '아파트'},
                    color='평균가격(억)',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig2_59, use_container_width=True)
            
            # 84m² 차트
            lease_84 = lease_avg[(lease_avg['면적(m²)'] >= 81) & (lease_avg['면적(m²)'] <= 87)]
            if not lease_84.empty:
                fig2_84 = px.bar(
                    lease_84,
                    x='아파트명',
                    y='평균가격(억)',
                    title='84m² 아파트별 평균 전세가',
                    labels={'평균가격(억)': '평균 전세가 (억원)', '아파트명': '아파트'},
                    color='평균가격(억)',
                    color_continuous_scale='Purples'
                )
                st.plotly_chart(fig2_84, use_container_width=True)
        else:
            st.info("전세 데이터가 없습니다.")
    
    with col3:
        st.markdown("##### 투자금 (매매가-전세가)")
        # 면적별로 평균 매매가와 평균 전세가를 계산하여 투자금 산출
        if not sale_df.empty and not lease_df.empty:
            investment_data = []
            for area in filtered_df['면적_m2'].unique():
                area_sale = sale_df[sale_df['면적_m2'] == area]['매매가_억']
                area_lease = lease_df[lease_df['면적_m2'] == area]['전세가_억']
                
                if not area_sale.empty and not area_lease.empty:
                    investment_data.append({
                        '면적(m²)': area,
                        '평균투자금(억)': round(area_sale.mean() - area_lease.mean(), 1),
                        '최소투자금(억)': round(area_sale.min() - area_lease.max(), 1),
                        '최대투자금(억)': round(area_sale.max() - area_lease.min(), 1),
                    })
            
            if investment_data:
                investment_df = pd.DataFrame(investment_data).set_index('면적(m²)')
                st.dataframe(investment_df, use_container_width=True)
            else:
                st.info("투자금 계산을 위한 데이터가 부족합니다.")
        else:
            st.info("투자금 계산을 위해 매매/전세 데이터가 모두 필요합니다.")

with tab3:
    st.subheader("🏢 아파트별 현황")
    
    # 아파트별 통계 테이블
    apt_stats = filtered_df.groupby('아파트명').agg({
        '세대수': 'first',
        '연식': 'first',
        '건축년도': 'first',
        '매매가_억': lambda x: f"{x[x>0].mean():.1f}" if (x>0).any() else "-",
        '전세가_억': lambda x: f"{x[x>0].mean():.1f}" if (x>0).any() else "-",
    }).reset_index()
    
    apt_stats.columns = ['아파트명', '세대수', '연식', '건축년도', '평균매매가(억)', '평균전세가(억)']
    
    st.dataframe(
        apt_stats,
        use_container_width=True,
        hide_index=True
    )
    
    # 아파트별 매물 수
    apt_count = filtered_df.groupby('아파트명').size().reset_index(name='매물수')
    
    fig3 = px.bar(
        apt_count,
        x='아파트명',
        y='매물수',
        title='아파트별 매물 수',
        labels={'아파트명': '아파트', '매물수': '매물 수'}
    )
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("💾 데이터 내보내기")
    
    st.write("**사용자 요청 컬럼 형식**으로 CSV 다운로드")
    
    # Export용 데이터프레임
    export_df = filtered_df.copy()
    export_df['거래유형'] = export_df['transaction_type'].map({'SALE': '매매', 'LEASE': '전세'})
    
    # 컬럼 선택 및 순서 지정
    export_cols = ['아파트명', '세대수', '연식', '면적_m2', '매매가_억', '전세가_억', '타입', '거래유형', '층수', 'floor', '방향']
    final_export = export_df[export_cols].copy()
    final_export.columns = ['아파트명', '세대수', '연식(년)', '면적(m²)', '매매가(억)', '전세가(억)', '타입', '거래유형', '층수', '층표시', '방향']
    
    # CSV 생성
    csv = final_export.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📥 CSV 다운로드 (아파트명, 세대수, 연식, 면적, 매매가, 전세가, 타입)",
        data=csv,
        file_name=f"부동산_데이터_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary"
    )
    
    st.success(f"✅ 총 {len(final_export):,}개 매물 데이터")
    
    # 미리보기
    st.write("**다운로드 데이터 미리보기:**")
    st.dataframe(final_export.head(10), use_container_width=True, hide_index=True)

# 푸터
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"📅 수집일시: {df['collected_at'].max()}" if not df.empty else "")
with col2:
    st.caption(f"🏢 총 {df['아파트명'].nunique()}개 아파트")
with col3:
    st.caption(f"📊 총 {len(df):,}개 매물")