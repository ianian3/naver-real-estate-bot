import streamlit as st
from src.database import RealEstateDB
from src.auth import UserManager
from src.analyzer import get_all_area_summaries, format_price_display
import plotly.express as px
import pandas as pd
from datetime import datetime
import json
import tempfile
import os
import subprocess
import time
import extra_streamlit_components as stx
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="부동산 데이터 분석",
    page_icon="🏢",
    layout="wide"
)

# 🆕 자동 업로드 감지 및 처리
pending_data_json = components.html("""
<script>
// LocalStorage에서 pending_upload 확인 및 반환
function getPendingUpload() {
    const pendingUpload = localStorage.getItem('pending_upload');
    if (pendingUpload) {
        console.log('Pending upload detected!');
        // 플래그 제거
        localStorage.removeItem('pending_upload');
        return pendingUpload;
    }
    return null;
}

// Streamlit으로 데이터 반환
const data = getPendingUpload();
if (data) {
    // return을 통해 Python으로 데이터 전달
    window.parent.postMessage({streamlitData: data}, '*');
}
</script>
""", height=0)

# LocalStorage에서 가져온 데이터 처리
if 'pending_upload_check' not in st.session_state:
    st.session_state.pending_upload_check = True
    
# Streamlit 컴포넌트로부터 데이터를 직접 받을 수 없으므로
# 사용자가 버튼을 눌러 수동으로 확인하도록 변경

# ================================
# 사용자 인증 (쿠키 기반 세션 유지)
# ================================

from streamlit_cookies_controller import CookieController

# 쿠키 컨트롤러 초기화
controller = CookieController()

# 세션 상태 초기화
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

user_manager = UserManager()

# 쿠키에서 자동 로그인 시도
if not st.session_state.authenticated:
    saved_username = controller.get('session_user')
    if saved_username:
        user = user_manager.get_user_by_username(saved_username)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user

# 로그인되지 않은 경우
if not st.session_state.authenticated:
    st.title("🏢 네이버 부동산 분석 서비스")
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    with tab1:
        st.subheader("로그인")
        login_username = st.text_input("아이디", key="login_username")
        login_password = st.text_input("비밀번호", type="password", key="login_password")
        
        if st.button("로그인", type="primary"):
            user = user_manager.verify_user(login_username, login_password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                # 쿠키에 사용자명 저장
                controller.set('session_user', login_username)
                st.success(f"환영합니다, {user['username']}님!")
                time.sleep(0.5)  # 쿠키 저장 대기
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
    
    with tab2:
        st.subheader("회원가입")
        signup_username = st.text_input("아이디", key="signup_username")
        signup_email = st.text_input("이메일", key="signup_email")
        signup_password = st.text_input("비밀번호", type="password", key="signup_password")
        signup_password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
        
        if st.button("가입하기", type="primary"):
            if not signup_username or not signup_email or not signup_password:
                st.error("모든 항목을 입력해주세요.")
            elif signup_password != signup_password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(signup_password) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            else:
                if user_manager.create_user(signup_username, signup_email, signup_password):
                    st.success("회원가입 완료! 로그인해주세요.")
                else:
                    st.error("이미 존재하는 아이디 또는 이메일입니다.")
    
    st.stop()

# ================================
# 로그인 후 메인 앱
# ================================

# 상단 사용자 정보 및 로그아웃
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("🏢 네이버 부동산 가격 분석")
with col2:
    user = st.session_state.user
    plan_badge = "🆓 무료" if user['plan'] == 'free' else "⭐ 프리미엄"
    st.info(f"👤 {user['username']} ({plan_badge})")
with col3:
    if st.button("🚪 로그아웃"):
        st.session_state.authenticated = False
        st.session_state.user = None
        # 쿠키 삭제
        controller.remove('session_user')
        st.rerun()

# DB 연결 (파일 업로드 전에 먼저 정의)
# 캐시 제거 - 데이터 업데이트가 즉시 반영되도록 함
def get_db():
    return RealEstateDB("data/real_estate.db")

db = get_db()

# ================================
# 사이드바 - 관심 단지 관리
# ================================

st.sidebar.header("⭐ 관심 단지 관리")

user = st.session_state.user
user_id = user['id']
max_watchlist = user['max_watchlist']

# 현재 관심 단지 개수
current_watchlist = user_manager.get_watchlist(user_id)
watchlist_count = len(current_watchlist)

# 사용량 표시
if watchlist_count >= max_watchlist:
    st.sidebar.warning(f"⚠️ {watchlist_count}/{max_watchlist} 사용 중 (최대)")
else:
    st.sidebar.info(f"📊 {watchlist_count}/{max_watchlist} 사용 중")

# 관심 단지 목록
if current_watchlist:
    st.sidebar.subheader("📋 현재 관심 단지")
    for item in current_watchlist:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.write(f"🏢 {item['complex_name']}")
        with col2:
            if st.button("🗑️", key=f"remove_{item['complex_no']}"):
                if user_manager.remove_from_watchlist(user_id, item['complex_no']):
                    st.success(f"{item['complex_name']} 제거 완료!")
                    st.rerun()
                else:
                    st.error("제거 실패")
else:
    st.sidebar.info("관심 단지가 없습니다.")

# 관심 단지 추가
st.sidebar.subheader("➕ 관심 단지 추가")

if watchlist_count >= max_watchlist:
    st.sidebar.error(f"⚠️ 무료 플랜은 최대 {max_watchlist}개까지 추적 가능합니다.")
    if user['plan'] == 'free':
        st.sidebar.info("💡 프리미엄 플랜으로 업그레이드하면 무제한 추적!")
        if st.sidebar.button("🚀 업그레이드", type="primary"):
            st.sidebar.info("결제 기능은 곧 추가됩니다!")
else:
    # DB에서 모든 단지 목록 가져오기
    all_complexes_query = "SELECT DISTINCT complex_no, complex_name FROM complexes ORDER BY complex_name"
    all_complexes_df = pd.read_sql_query(all_complexes_query, db.conn)
    
    # 이미 추가된 단지 제외
    watchlist_nos = [w['complex_no'] for w in current_watchlist]
    available_complexes = all_complexes_df[~all_complexes_df['complex_no'].isin(watchlist_nos)]
    
    if not available_complexes.empty:
        complex_options = {row['complex_name']: row['complex_no'] for _, row in available_complexes.iterrows()}
        
        selected_name = st.sidebar.selectbox(
            "단지 선택",
            options=list(complex_options.keys()),
            key="watchlist_select"
        )
        
        if st.sidebar.button("➕ 추가", type="primary"):
            selected_no = complex_options[selected_name]
            if user_manager.add_to_watchlist(user_id, selected_no, selected_name):
                st.sidebar.success(f"✅ {selected_name} 추가 완료!")
                st.rerun()
            else:
                st.sidebar.error("추가 실패 (이미 존재)")
    else:
        st.sidebar.info("추가 가능한 단지가 없습니다.")

st.sidebar.markdown("---")

# ================================
# 사이드바 - 알림 설정
# ================================

st.sidebar.header("🔔 알림 설정")

# 이메일 설정 확인
import os
from dotenv import load_dotenv
load_dotenv()

has_email_config = bool(os.getenv('EMAIL_ADDRESS') and os.getenv('EMAIL_PASSWORD'))

if not has_email_config:
    st.sidebar.warning("⚠️ 이메일 설정이 필요합니다")
    with st.sidebar.expander("📝 설정 방법"):
        st.write("""
        1. `.env` 파일 생성
        2. Gmail 앱 비밀번호 발급
        3. 환경변수 설정
        
        자세한 내용: `EMAIL_SETUP.md` 참고
        """)
else:
    st.sidebar.success("✅ 이메일 설정 완료")
    
    # 테스트 이메일 발송
    if st.sidebar.button("📧 테스트 이메일"):
        from src.notifications import EmailNotifier
        notifier = EmailNotifier()
        
        user_email = st.session_state.user['email']
        if notifier.send_test_email(user_email):
            st.sidebar.success(f"✅ 발송 완료!")
        else:
            st.sidebar.error("❌ 발송 실패")

st.sidebar.markdown("---")

# ================================
# 사이드바 - 데이터베이스 관리
# ================================
st.sidebar.header("🗄️ 데이터베이스 관리")

# 현재 데이터 현황
try:
    db_stats_cursor = db.conn.execute("SELECT COUNT(*) FROM complexes")
    complex_count = db_stats_cursor.fetchone()[0]
    db_stats_cursor = db.conn.execute("SELECT COUNT(*) FROM prices")
    price_count = db_stats_cursor.fetchone()[0]
    st.sidebar.info(f"📊 단지: {complex_count}개 | 매물: {price_count}개")
except:
    st.sidebar.warning("⚠️ DB 통계 조회 실패")

# 초기화 확인 체크박스와 버튼
confirm_reset = st.sidebar.checkbox("⚠️ 정말 초기화하시겠습니까?", key="confirm_db_reset")

if st.sidebar.button("🗑️ 데이터베이스 초기화", type="secondary", disabled=not confirm_reset):
    try:
        # 모든 가격 데이터 삭제
        db.conn.execute("DELETE FROM prices")
        # 모든 단지 정보 삭제
        db.conn.execute("DELETE FROM complexes")
        db.conn.commit()
        st.sidebar.success("✅ 데이터베이스 초기화 완료!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"❌ 초기화 실패: {str(e)}")

st.sidebar.markdown("---")

# ================================
# 사이드바 - 파일 업로드 기능
# ================================
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
        
        # 두 가지 JSON 형식 지원:
        # 형식 1: {"metadata": {...}, "listings": [...]}
        # 형식 2: {"metadata": {...}, "complexes": [{"metadata": {...}, "listings": [...]}]}
        
        if 'complexes' in json_data and isinstance(json_data['complexes'], list):
            # 형식 2: 여러 단지가 포함된 경우
            complexes_list = json_data['complexes']
        else:
            # 형식 1: 단일 단지 데이터
            complexes_list = [json_data]
        
        # 각 단지 처리
        for complex_data in complexes_list:
            # 메타데이터 추출
            metadata = complex_data.get('metadata', {})
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
            listings = complex_data.get('listings', [])
            sale_count = 0
            lease_count = 0
            
            for listing in listings:
                area = listing.get('exclusive_area', 0)
                area_type = listing.get('area_type', '')  # 원본 타입명 사용 (예: 86B/59m², 111A/84m²)
                
                # 면적 필터링 (59m², 75m², 84m²)
                if not (56 <= area <= 62 or 72 <= area <= 78 or 81 <= area <= 87):
                    continue
                
                # 매매 데이터 - count 값을 int로 변환하여 비교
                sale_price_val = listing.get('sale_price', 0)
                sale_count_val = int(listing.get('sale_count', 0)) if str(listing.get('sale_count', 0)).isdigit() else 0
                
                if sale_price_val > 0 and sale_count_val > 0:
                    floor_str = listing.get('sale_floor', '')
                    floor_num = 15 if '고' in floor_str else 9 if '중' in floor_str else 5
                    
                    if floor_num >= 4:
                        sale_df = pd.DataFrame([{
                            '면적타입': area_type,
                            '전용면적': area,
                            '거래유형': 'SALE',
                            '층': floor_str,
                            '층수': floor_num,
                            '방향': '',
                            '가격': sale_price_val,  # 이미 만원 단위
                            '보증금': 0,
                        }])
                        db.save_prices(sale_df, complex_no)
                        sale_count += 1
                
                # 전세 데이터 - count 값을 int로 변환하여 비교
                lease_price_val = listing.get('lease_price', 0)
                lease_count_val = int(listing.get('lease_count', 0)) if str(listing.get('lease_count', 0)).isdigit() else 0
                
                if lease_price_val > 0 and lease_count_val > 0:
                    floor_str = listing.get('lease_floor', '')
                    floor_num = 15 if '고' in floor_str else 9 if '중' in floor_str else 5
                    
                    if floor_num >= 4:
                        lease_df = pd.DataFrame([{
                            '면적타입': area_type,
                            '전용면적': area,
                            '거래유형': 'LEASE',
                            '층': floor_str,
                            '층수': floor_num,
                            '방향': '',
                            '가격': 0,
                            '보증금': lease_price_val,  # 이미 만원 단위
                        }])
                        db.save_prices(lease_df, complex_no)
                        lease_count += 1
            
            st.sidebar.success(f"✅ {complex_name} 가져오기 성공!")
            st.sidebar.info(f"매매 {sale_count}개, 전세 {lease_count}개")
            
            # 🆕 가격 히스토리 자동 저장
            db.save_daily_summary(complex_no)
        
        # 캐시 클리어 및 즉시 새로고침
        st.cache_data.clear()
        st.success("✅ 데이터가 업데이트되었습니다! 페이지를 새로고침합니다...")
        st.rerun()
        
    except Exception as e:
        st.sidebar.error(f"❌ 오류: {str(e)}")
        st.error(f"상세 오류: {str(e)}")

st.sidebar.divider()

# ================================
# 사이드바 - 데이터 필터 설정
# ================================

st.sidebar.header("🔍 데이터 필터")

# 전체/관심 단지 토글
filter_mode = st.sidebar.radio(
    "표시할 단지",
    options=["전체 단지", "내 관심 단지만"],
    index=0,
    help="메인 화면에 표시할 데이터를 선택하세요"
)

st.sidebar.markdown("---")

# ================================
# 메인 영역 - 데이터 로드 및 필터링
# ================================

def load_formatted_data(complex_no=None):
    """데이터 로드 (항상 새 DB 연결로 최신 데이터 반영)"""
    # 매번 새로운 DB 연결을 생성하여 최신 데이터 보장
    fresh_db = RealEstateDB("data/real_estate.db")
    
    query = """
    SELECT 
        c.complex_no,
        c.complex_name as 아파트명,
        c.address as 주소,
        c.total_households as 세대수,
        c.build_year as 연식,
        p.area_type as 면적타입,
        p.exclusive_area as 면적_m2,
        CASE 
            WHEN p.transaction_type = 'SALE' THEN ROUND(p.price / 10000.0, 2)
            ELSE 0
        END as 매매가_억,
        CASE 
            WHEN p.transaction_type = 'LEASE' THEN ROUND(p.deposit / 10000.0, 2)
            ELSE 0
        END as 전세가_억,
        p.transaction_type as 거래유형,
        p.floor,
        p.floor_number as 층수,
        p.direction as 방향,
        p.collected_at,
        CASE p.transaction_type WHEN 'SALE' THEN '매매' WHEN 'LEASE' THEN '전세' ELSE '기타' END as 타입
    FROM prices p
    JOIN complexes c ON p.complex_no = c.complex_no
    """
    
    params = []
    
    # 특정 단지 필터링
    if complex_no:
        query += " WHERE c.complex_no = ?"
        params.append(complex_no)
    
    query += " ORDER BY c.complex_name, p.area_type, p.transaction_type"
    
    try:
        result = pd.read_sql_query(query, fresh_db.conn, params=params)
        fresh_db.close()  # 연결 종료
        return result
    except Exception as e:
        print(f"데이터 로드 오류: {e}")
        fresh_db.close()
        return pd.DataFrame()

# 데이터 로드
df = load_formatted_data()

# 관심 단지 필터링
if filter_mode == "내 관심 단지만" and current_watchlist:
    watchlist_nos = [w['complex_no'] for w in current_watchlist]
    df = df[df['complex_no'].isin(watchlist_nos)]
    st.info(f"📌 {len(current_watchlist)}개 관심 단지 데이터만 표시 중")
elif filter_mode == "내 관심 단지만" and not current_watchlist:
    st.warning("⚠️ 관심 단지가 없습니다. 사이드바에서 추가해주세요!")
    df = pd.DataFrame()

# 데이터가 없는 경우 처리
if df.empty:
    st.warning("데이터가 없습니다. JSON 파일을 업로드하거나 관심 단지를 추가해주세요.")
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
    filtered_df = filtered_df[filtered_df['거래유형'] == 'SALE']
elif selected_type == "전세만":
    filtered_df = filtered_df[filtered_df['거래유형'] == 'LEASE']

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
    sale_count = len(filtered_df[filtered_df['거래유형'] == 'SALE'])
    st.metric("매매", f"{sale_count:,}개")

with col3:
    lease_count = len(filtered_df[filtered_df['거래유형'] == 'LEASE'])
    st.metric("전세", f"{lease_count:,}개")

with col4:
    complex_count = filtered_df['아파트명'].nunique()
    st.metric("단지 수", f"{complex_count}개")

st.divider()

# 탭 생성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📋 매물 리스트", "📊 가격 분석", "📈 가격 추이", "🏢 아파트별 통계", "💾 내보내기", "🎯 저환수원리"])

with tab1:
    st.subheader("📋 매물 목록 (사용자 요청 컬럼)")
    
    # 거래유형이 이미 별칭으로 있으므로 추가 변환 불필요
    display_df = filtered_df.copy()
    
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
    st.subheader("📈 가격 변동 추이")
    
    # 단지 선택
    all_complexes = filtered_df['아파트명'].unique().tolist()
    
    if not all_complexes:
        st.warning("가격 추이를 확인할 단지가 없습니다.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # 단지명 → 단지번호 매핑
            complex_name_to_no = dict(zip(
                filtered_df['아파트명'].unique(),
                filtered_df.groupby('아파트명')['complex_no'].first()
            ))
            selected_complex_name = st.selectbox(
                "🏢 단지 선택",
                options=all_complexes,
                key="trend_complex_select"
            )
            selected_complex_no = complex_name_to_no.get(selected_complex_name)
        
        with col2:
            # 면적 선택
            if selected_complex_no:
                area_types = db.get_area_types(selected_complex_no)
                if area_types:
                    area_options = ["전체"] + area_types
                    selected_area_type = st.selectbox(
                        "📐 면적 선택",
                        options=area_options,
                        key="trend_area_select"
                    )
                else:
                    selected_area_type = "전체"
                    st.info("면적 데이터 없음")
            else:
                selected_area_type = "전체"
        
        with col3:
            # 기간 선택
            period_options = {"1주": 7, "1개월": 30, "3개월": 90, "6개월": 180, "1년": 365, "전체": 9999}
            selected_period = st.selectbox(
                "📅 기간",
                options=list(period_options.keys()),
                index=2,  # 기본값: 3개월
                key="trend_period_select"
            )
            days = period_options[selected_period]
        
        # 가격 히스토리 조회
        if selected_complex_no:
            area_param = None if selected_area_type == "전체" else selected_area_type
            history_df = db.get_price_history(selected_complex_no, area_param, days=days)
            
            if not history_df.empty:
                # 가격 변동 정보
                change_info = db.get_price_change(selected_complex_no, area_param, compare_days=min(days, 30))
                
                # 메트릭 카드
                mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                
                with mcol1:
                    if change_info and 'sale_current' in change_info:
                        sale_display = f"{change_info['sale_current'] / 10000:.1f}억"
                        sale_delta = f"{change_info.get('sale_change_pct', 0):.1f}%"
                        st.metric("📊 평균 매매가", sale_display, sale_delta)
                    else:
                        st.metric("📊 평균 매매가", "-", "데이터 부족")
                
                with mcol2:
                    if change_info and 'lease_current' in change_info:
                        lease_display = f"{change_info['lease_current'] / 10000:.1f}억"
                        lease_delta = f"{change_info.get('lease_change_pct', 0):.1f}%"
                        st.metric("📊 평균 전세가", lease_display, lease_delta)
                    else:
                        st.metric("📊 평균 전세가", "-", "데이터 부족")
                
                with mcol3:
                    if change_info and 'gap_current' in change_info:
                        gap_display = f"{change_info['gap_current'] / 10000:.1f}억"
                        gap_delta = f"{change_info.get('gap_change', 0) / 10000:.1f}억"
                        st.metric("💰 갭 (투자금)", gap_display, gap_delta, delta_color="inverse")
                    else:
                        st.metric("💰 갭 (투자금)", "-", "데이터 부족")
                
                with mcol4:
                    latest = history_df.iloc[-1] if not history_df.empty else None
                    if latest is not None and latest.get('lease_ratio'):
                        st.metric("📈 전세가율", f"{latest['lease_ratio']:.1f}%", "")
                    else:
                        st.metric("📈 전세가율", "-", "")
                
                st.divider()
                
                # 가격 추이 차트
                st.markdown("#### 📊 가격 변동 차트")
                
                # 데이터 전처리
                chart_df = history_df.copy()
                chart_df['매매가(억)'] = chart_df['sale_avg_price'].apply(lambda x: x / 10000 if x else None)
                chart_df['전세가(억)'] = chart_df['lease_avg_price'].apply(lambda x: x / 10000 if x else None)
                chart_df['날짜'] = pd.to_datetime(chart_df['record_date'])
                
                # 멀티라인 차트
                fig = px.line(
                    chart_df,
                    x='날짜',
                    y=['매매가(억)', '전세가(억)'],
                    title=f"{selected_complex_name} 가격 추이 ({selected_period})",
                    labels={'value': '가격 (억원)', 'variable': '거래유형'},
                    markers=True
                )
                fig.update_layout(
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    hovermode='x unified'
                )
                fig.update_traces(line=dict(width=2))
                st.plotly_chart(fig, use_container_width=True)
                
                # 면적별 상세 (전체 선택 시)
                if selected_area_type == "전체" and len(history_df['area_type'].unique()) > 1:
                    st.markdown("#### 📐 면적별 가격 추이")
                    
                    area_chart_df = history_df.copy()
                    area_chart_df['매매가(억)'] = area_chart_df['sale_avg_price'].apply(lambda x: x / 10000 if x else None)
                    area_chart_df['날짜'] = pd.to_datetime(area_chart_df['record_date'])
                    
                    fig2 = px.line(
                        area_chart_df,
                        x='날짜',
                        y='매매가(억)',
                        color='area_type',
                        title=f"{selected_complex_name} 면적별 매매가 추이",
                        labels={'매매가(억)': '매매가 (억원)', 'area_type': '면적'},
                        markers=True
                    )
                    fig2.update_layout(height=350)
                    st.plotly_chart(fig2, use_container_width=True)
                
                # 히스토리 데이터 테이블
                with st.expander("📋 상세 데이터 보기"):
                    display_history = history_df[['record_date', 'area_type', 'sale_avg_price', 'lease_avg_price', 'gap_investment', 'lease_ratio', 'sale_count', 'lease_count']].copy()
                    display_history.columns = ['날짜', '면적', '매매평균(만원)', '전세평균(만원)', '갭(만원)', '전세가율(%)', '매매수', '전세수']
                    st.dataframe(display_history, use_container_width=True, hide_index=True)
            else:
                st.info("📭 아직 가격 히스토리가 없습니다.")
                st.write("""
                **가격 추이 데이터 수집 방법:**
                1. JSON 파일을 업로드하면 자동으로 당일 가격이 기록됩니다
                2. 매일 또는 정기적으로 데이터를 업로드하면 시간에 따른 변화를 확인할 수 있습니다
                """)

with tab4:
    st.subheader("🏢 아파트별 현황")
    
    # 아파트별 통계 테이블
    apt_stats = filtered_df.groupby('아파트명').agg({
        '세대수': 'first',
        '연식': 'first',
        '매매가_억': lambda x: f"{x[x>0].mean():.1f}" if (x>0).any() else "-",
        '전세가_억': lambda x: f"{x[x>0].mean():.1f}" if (x>0).any() else "-",
    }).reset_index()
    
    apt_stats.columns = ['아파트명', '세대수', '연식', '평균매매가(억)', '평균전세가(억)']
    
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

with tab5:
    st.subheader("💾 데이터 내보내기")
    
    st.write("**사용자 요청 컬럼 형식**으로 CSV 다운로드")
    
    # Export용 데이터프레임
    export_df = filtered_df.copy()
    
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

# ================================
# Tab 6: 저환수원리 분석
# ================================
with tab6:
    st.subheader("🎯 저환수원리 분석")
    st.caption("월급쟁이부자들 투자 기준으로 매물을 분석해보세요.")
    
    # 분석 대상 단지 정보
    st.markdown("### 🏠 분석 대상 단지")
    target_col1, target_col2 = st.columns(2)
    with target_col1:
        target_name = st.text_input("단지명", placeholder="예: 개포자이 84A", key="target_name")
    with target_col2:
        target_area = st.selectbox("면적", ["59m²", "75m²", "84m²"], key="target_area")
    
    st.divider()
    
    # ========== 저평가 ==========
    st.markdown("### 🟢 저 (저평가) - 비슷한 가치 단지 5개 비교")
    st.caption("동일 생활권/비슷한 조건의 단지 시세를 입력하세요 (만원 단위)")
    
    compare_data = []
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.markdown(f"**단지 {i+1}**")
            name = st.text_input("단지명", key=f"comp_name_{i}", placeholder=f"단지{i+1}")
            sale = st.number_input("매매가(만원)", key=f"comp_sale_{i}", min_value=0, step=1000)
            lease = st.number_input("전세가(만원)", key=f"comp_lease_{i}", min_value=0, step=1000)
            if sale > 0:
                compare_data.append({'name': name or f'단지{i+1}', 'sale': sale, 'lease': lease})
    
    # 대상 단지 가격
    st.markdown("**🎯 대상 단지 가격**")
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        target_sale = st.number_input("대상 매매가(만원)", key="target_sale", min_value=0, step=1000)
    with tcol2:
        target_lease = st.number_input("대상 전세가(만원)", key="target_lease", min_value=0, step=1000)
    
    # 저평가 계산
    underval_score = 50  # 기본값
    underval_comment = ""
    if compare_data and target_sale > 0:
        avg_compare_sale = sum(c['sale'] for c in compare_data) / len(compare_data)
        deviation = ((target_sale - avg_compare_sale) / avg_compare_sale) * 100
        
        if deviation < -10:
            underval_score = 90
            underval_comment = f"🟢 주변 대비 {abs(deviation):.1f}% 저렴 (매우 좋음)"
        elif deviation < -5:
            underval_score = 70
            underval_comment = f"🟢 주변 대비 {abs(deviation):.1f}% 저렴 (좋음)"
        elif deviation < 0:
            underval_score = 55
            underval_comment = f"🟡 주변 대비 {abs(deviation):.1f}% 저렴 (보통)"
        else:
            underval_score = 35
            underval_comment = f"🔴 주변 대비 {deviation:.1f}% 비쌈 (주의)"
    
    st.divider()
    
    # ========== 환금성 ==========
    st.markdown("### 🟡 환 (환금성) - 팔리는 매물인가?")
    
    hcol1, hcol2 = st.columns(2)
    with hcol1:
        is_large_complex = st.checkbox("✅ 300세대 이상 단지", value=True, key="large_complex")
        is_brand = st.checkbox("✅ 대형 브랜드 (자이, 래미안 등)", value=False, key="brand")
        is_subway = st.checkbox("✅ 역세권 (도보 10분 이내)", value=False, key="subway")
    
    with hcol2:
        exclude_low = st.checkbox("✅ 1~3층 저층 제외 매물", value=True, key="exclude_low")
        exclude_top = st.checkbox("✅ 탑층 제외 매물", value=True, key="exclude_top")
        is_south = st.checkbox("✅ 남향/남동향", value=False, key="south")
    
    # 환금성 점수 계산
    liquidity_score = 40
    if is_large_complex: liquidity_score += 20
    if is_brand: liquidity_score += 15
    if is_subway: liquidity_score += 10
    if exclude_low: liquidity_score += 5
    if exclude_top: liquidity_score += 5
    if is_south: liquidity_score += 5
    liquidity_score = min(liquidity_score, 100)
    
    st.divider()
    
    # ========== 수익률 ==========
    st.markdown("### 🟢 수 (수익률) - 투자금 대비 수익")
    
    rcol1, rcol2, rcol3 = st.columns(3)
    with rcol1:
        expected_peak = st.number_input("예상 전고점(만원)", key="expected_peak", min_value=0, step=1000,
                                        help="이 단지가 도달할 수 있는 예상 최고가")
    with rcol2:
        if target_sale > 0 and target_lease > 0:
            gap = target_sale - target_lease
            st.metric("투자금 (갭)", f"{gap/10000:.1f}억")
        else:
            gap = 0
            st.metric("투자금 (갭)", "-")
    with rcol3:
        if expected_peak > 0 and target_sale > 0 and gap > 0:
            upside = expected_peak - target_sale
            roi = (upside / gap) * 100
            st.metric("예상 수익률", f"{roi:.0f}%", f"+{upside/10000:.1f}억")
        else:
            roi = 0
            st.metric("예상 수익률", "-")
    
    # 수익률 점수
    if roi >= 100:
        return_score = 90
    elif roi >= 50:
        return_score = 70
    elif roi >= 20:
        return_score = 50
    else:
        return_score = 30
    
    st.divider()
    
    # ========== 원금보존 ==========
    st.markdown("### 🟡 원 (원금보존) - 전세가율 분석")
    
    if target_sale > 0 and target_lease > 0:
        lease_ratio = (target_lease / target_sale) * 100
        
        if lease_ratio <= 60:
            principal_score = 90
            principal_comment = "🟢 매우 안전 - 역전세 위험 낮음"
        elif lease_ratio <= 70:
            principal_score = 70
            principal_comment = "🟢 안전 - 적정 전세가율"
        elif lease_ratio <= 80:
            principal_score = 50
            principal_comment = "🟡 주의 - 전세가율 다소 높음"
        else:
            principal_score = 30
            principal_comment = "🔴 위험 - 역전세 가능성 있음"
        
        st.metric("전세가율", f"{lease_ratio:.1f}%")
        st.caption(principal_comment)
    else:
        principal_score = 50
        st.info("매매가/전세가를 입력하면 자동 계산됩니다")
    
    st.divider()
    
    # ========== 리스크 ==========
    st.markdown("### 🔴 리 (리스크 관리) - 입주물량 & 연식")
    
    riskcol1, riskcol2 = st.columns(2)
    with riskcol1:
        supply_grade = st.selectbox(
            "향후 1년 입주물량",
            options=["S: 입주 거의 없음", "A: 적음", "B: 보통", "C: 많음 (주의)"],
            key="supply_grade"
        )
    with riskcol2:
        build_age = st.number_input("연식 (년)", min_value=0, max_value=50, value=10, key="build_age")
    
    # 리스크 점수
    supply_scores = {"S: 입주 거의 없음": 25, "A: 적음": 15, "B: 보통": 5, "C: 많음 (주의)": -10}
    risk_score = 50 + supply_scores.get(supply_grade, 0)
    
    # 연식 보너스
    if 5 <= build_age <= 15:
        risk_score += 20  # 최적 연식
    elif build_age < 5:
        risk_score += 10  # 신축
    elif build_age >= 30:
        risk_score += 15  # 재건축 기대
    
    risk_score = max(min(risk_score, 100), 0)
    
    st.divider()
    
    # ========== 종합 결과 ==========
    st.markdown("### 🏆 종합 분석 결과")
    
    # 가중 평균
    weights = {'저': 0.25, '환': 0.15, '수': 0.20, '원': 0.25, '리': 0.15}
    scores = {
        '저': underval_score,
        '환': liquidity_score,
        '수': return_score,
        '원': principal_score,
        '리': risk_score
    }
    total_score = sum(scores[k] * weights[k] for k in weights)
    
    # 등급 산정
    if total_score >= 80:
        grade = "⭐⭐⭐⭐⭐"
        recommendation = "적극 추천"
        grade_color = "green"
    elif total_score >= 65:
        grade = "⭐⭐⭐⭐☆"
        recommendation = "투자 고려"
        grade_color = "blue"
    elif total_score >= 50:
        grade = "⭐⭐⭐☆☆"
        recommendation = "신중 검토"
        grade_color = "orange"
    else:
        grade = "⭐⭐☆☆☆"
        recommendation = "투자 주의"
        grade_color = "red"
    
    # 결과 카드
    result_cols = st.columns(5)
    labels = ['저평가', '환금성', '수익률', '원금보존', '리스크']
    keys = ['저', '환', '수', '원', '리']
    for i, (label, key) in enumerate(zip(labels, keys)):
        with result_cols[i]:
            score = scores[key]
            emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.metric(f"{emoji} {label}", f"{score}점")
    
    # 총점
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 15px; margin: 20px 0;">
        <h2 style="color: white; margin: 0;">{target_name or '대상 단지'}</h2>
        <h1 style="color: white; font-size: 3rem; margin: 10px 0;">{grade}</h1>
        <h3 style="color: white; margin: 0;">종합 {total_score:.0f}점 - {recommendation}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 상세 코멘트
    with st.expander("📝 상세 분석 코멘트"):
        st.write(f"**저평가**: {underval_comment if underval_comment else '비교 데이터 입력 필요'}")
        st.write(f"**환금성**: 선택된 조건 {sum([is_large_complex, is_brand, is_subway, exclude_low, exclude_top, is_south])}개 충족")
        st.write(f"**수익률**: 투자금 대비 예상 수익률 {roi:.0f}%" if roi > 0 else "**수익률**: 데이터 입력 필요")
        st.write(f"**원금보존**: {principal_comment if target_sale > 0 else '데이터 입력 필요'}")
        st.write(f"**리스크**: 입주물량 {supply_grade.split(':')[0]}등급, {build_age}년차")
    
    # AI 투자 분석 보고서 생성
    st.divider()
    st.markdown("### 📄 AI 투자 분석 보고서")
    
    if target_sale > 0 and target_lease > 0:
        if st.button("🤖 AI 분석 보고서 생성", type="primary", use_container_width=True):
            with st.spinner("AI가 투자 분석 보고서를 작성 중입니다..."):
                from src.report_generator import generate_investment_report
                
                # 분석 데이터 구성
                analysis_data = {
                    'target_name': target_name or '대상 단지',
                    'target_area': target_area,
                    'target_sale': target_sale,
                    'target_lease': target_lease,
                    'scores': scores,
                    'total_score': total_score,
                    'grade': grade,
                    'recommendation': recommendation,
                    'details': {
                        'underval_comment': underval_comment,
                        'liquidity_checks': sum([is_large_complex, is_brand, is_subway, exclude_low, exclude_top, is_south]),
                        'roi': roi,
                        'lease_ratio': (target_lease / target_sale * 100) if target_sale > 0 else 0,
                        'supply_grade': supply_grade,
                        'build_age': build_age
                    }
                }
                
                # 보고서 생성
                report = generate_investment_report(analysis_data)
                
                # 세션에 저장
                st.session_state['generated_report'] = report
                st.session_state['report_target'] = target_name or '대상단지'
        
        # 생성된 보고서 표시
        if 'generated_report' in st.session_state and st.session_state.get('generated_report'):
            st.success("✅ 보고서 생성 완료!")
            
            # 보고서 미리보기
            with st.expander("📋 보고서 미리보기", expanded=True):
                st.markdown(st.session_state['generated_report'])
            
            # 다운로드 버튼
            report_filename = f"투자분석_{st.session_state.get('report_target', '단지')}_{datetime.now().strftime('%Y%m%d')}.md"
            st.download_button(
                label="📥 보고서 다운로드 (Markdown)",
                data=st.session_state['generated_report'],
                file_name=report_filename,
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.info("💡 보고서를 생성하려면 먼저 매매가와 전세가를 입력하세요.")