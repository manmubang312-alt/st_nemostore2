import streamlit as st
import pandas as pd
import sqlite3
import json
import os
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import ast

# 페이지 설정
st.set_page_config(page_title="Nemo Store Dashboard", layout="wide")

# CSS 스타일 정의 (프리미엄 디자인)
def local_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8f9fa;
    }
    
    .stCard {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #eee;
    }
    
    .kpi-label {
        color: #6c757d;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .kpi-value {
        color: #212529;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* HTML Template Specific Styles */
    .detail-content {
        max-width: 600px;
        margin: auto;
        background: white;
        border: 1px solid #ddd;
    }
    
    .slide-image {
        width: 100%;
        height: 300px;
        object-fit: cover;
    }
    
    .price-container table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    
    .price-container th {
        text-align: left;
        padding: 10px;
        color: #444;
        border-bottom: 1px solid #eee;
    }
    
    .price-container td {
        text-align: right;
        padding: 10px;
        font-weight: bold;
        color: #d32f2f;
        border-bottom: 1px solid #eee;
    }
    
    .main-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 15px 0;
        padding: 0 15px;
    }
    
    .upper-title {
        color: #888;
        font-size: 0.9rem;
        margin-top: 20px;
        padding: 0 15px;
    }
    </style>
    """, unsafe_allow_html=True)

local_css()

# 데이터 로딩 함수
@st.cache_data
def load_data():
    db_path = os.path.join(os.getcwd(), 'data', 'nemo_store.db')
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM stores", conn)
    conn.close()
    
    # 리스트 형태의 컬럼 처리
    for col in ['smallPhotoUrls', 'originPhotoUrls']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x)
            
    return df

# 금액 변환 함수 (만원 단위 입력을 억/만원으로 표현)
def format_price(amount_manwon):
    if amount_manwon == 0:
        return "0"
    if amount_manwon >= 10000:
        eok = amount_manwon // 10000
        man = amount_manwon % 10000
        if man == 0:
            return f"{eok}억"
        else:
            return f"{eok}억 {man:,}만"
    return f"{amount_manwon:,}만"

# 메인 로직
def main():
    try:
        df = load_data()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return

    # 사이드바 필터링
    st.sidebar.title("🔍 필터")
    
    # 업종 필터
    all_categories = sorted(df['businessLargeCodeName'].unique().tolist())
    selected_categories = st.sidebar.multiselect("업종 선택", all_categories, default=all_categories)
    
    # 층수 필터
    all_floors = sorted(df['floor'].unique().tolist())
    selected_floors = st.sidebar.multiselect("층수 선택", all_floors, default=all_floors)
    
    # 보증금 범위 필터
    min_dep, max_dep = int(df['deposit'].min()), int(df['deposit'].max())
    deposit_range = st.sidebar.slider("보증금 범위 (만원)", min_dep, max_dep, (min_dep, max_dep))
    
    # 데이터 필터링 적용
    filtered_df = df[
        (df['businessLargeCodeName'].isin(selected_categories)) &
        (df['floor'].isin(selected_floors)) &
        (df['deposit'] >= deposit_range[0]) &
        (df['deposit'] <= deposit_range[1])
    ]

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 대시보드 (EDA)", "🏢 매물 리스트", "🔍 상세 정보"])

    with tab1:
        st.subheader("📈 전체 매물 통계")
        
        # KPI 카드
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stCard"><div class="kpi-label">총 매물 수</div><div class="kpi-value">{len(filtered_df)}건</div></div>', unsafe_allow_html=True)
        with col2:
            avg_deposit = filtered_df['deposit'].mean()
            st.markdown(f'<div class="stCard"><div class="kpi-label">평균 보증금</div><div class="kpi-value">{format_price(avg_deposit)}</div></div>', unsafe_allow_html=True)
        with col3:
            avg_rent = filtered_df['monthlyRent'].mean()
            st.markdown(f'<div class="stCard"><div class="kpi-label">평균 월세</div><div class="kpi-value">{format_price(avg_rent)}</div></div>', unsafe_allow_html=True)
        with col4:
            avg_premium = filtered_df['premium'].mean()
            st.markdown(f'<div class="stCard"><div class="kpi-label">평균 권리금</div><div class="kpi-value">{format_price(avg_premium)}</div></div>', unsafe_allow_html=True)

        # 시각화
        v_col1, v_col2 = st.columns(2)
        
        with v_col1:
            st.write("### 🏢 업종별 분포")
            cat_counts = filtered_df['businessLargeCodeName'].value_counts()
            fig, ax = plt.subplots(figsize=(10, 6))
            cat_counts.plot(kind='barh', ax=ax, color='#1f77b4')
            ax.set_xlabel('매물 수')
            st.pyplot(fig)
            
        with v_col2:
            st.write("### 💰 보증금 vs 월세 상관관계")
            fig = px.scatter(filtered_df, x='deposit', y='monthlyRent', color='businessLargeCodeName',
                             hover_data=['title', 'size'],
                             labels={'deposit': '보증금(만원)', 'monthlyRent': '월세(만원)'},
                             template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("📋 실시간 매물 목록")
        display_cols = ['title', 'businessMiddleCodeName', 'deposit', 'monthlyRent', 'premium', 'size', 'floor']
        # 예쁘게 표시하기 위해 금액 포맷팅
        display_df = filtered_df[display_cols].copy()
        display_df['deposit'] = display_df['deposit'].apply(format_price)
        display_df['monthlyRent'] = display_df['monthlyRent'].apply(format_price)
        display_df['premium'] = display_df['premium'].apply(format_price)
        st.dataframe(display_df, use_container_width=True)

    with tab3:
        if len(filtered_df) == 0:
            st.warning("조건에 맞는 매물이 없습니다.")
        else:
            selected_title = st.selectbox("상세 정보를 볼 매물을 선택하세요", filtered_df['title'].tolist())
            item = filtered_df[filtered_df['title'] == selected_title].iloc[0]
            
            # 상세 정보 렌더링 (HTML 기반)
            st.markdown(f"""
            <div class="detail-content">
                <div class="slides">
                    <img class="slide-image" src="{item['previewPhotoUrl']}" alt="매물 이미지">
                </div>
                <div class="title-wrapper">
                    <h6 class="upper-title">{item['businessMiddleCodeName']} • {item['floor']}층 • 전용 {item['size']}㎡</h6>
                    <h2 class="main-title">{item['title']}</h2>
                    <div class="tag-wrapper" style="padding: 0 15px;">
                        <span style="background:#f5f5f6; padding:5px; border-radius:4px; font-size:12px; color:#5c636b;">
                            {item['nearSubwayStation']}
                        </span>
                    </div>
                </div>
                <div class="price-container" style="padding: 0 15px;">
                    <table>
                        <tr style="color: #002e5b; font-weight:bold;">
                            <th>월세</th>
                            <td>{format_price(item['monthlyRent'])}원</td>
                        </tr>
                        <tr>
                            <th>보증금</th>
                            <td>{format_price(item['deposit'])}원</td>
                        </tr>
                        <tr>
                            <th>권리금</th>
                            <td>{format_price(item['premium'])}원</td>
                        </tr>
                        <tr>
                            <th>월 관리비</th>
                            <td>{format_price(item['maintenanceFee'])}원</td>
                        </tr>
                    </table>
                </div>
                <div class="info-section" style="padding: 15px; background: #fff;">
                    <h4 style="border-bottom: 2px solid #ddd; padding-bottom: 5px;">📍 매물 특징</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 10px 0;">🏢 층수: 지상 {item['floor']}층 / 전체 {item['groundFloor']}층</li>
                        <li style="margin: 10px 0;">📏 면적: {item['size']}㎡ (약 {round(item['size']/3.3057, 1)}평)</li>
                        <li style="margin: 10px 0;">🚉 교통: {item['nearSubwayStation']}</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 추가 이미지 갤러리 (있는 경우)
            if isinstance(item['originPhotoUrls'], list) and len(item['originPhotoUrls']) > 1:
                st.write("### 📸 추가 사진")
                cols = st.columns(3)
                for idx, url in enumerate(item['originPhotoUrls'][1:]):
                    with cols[idx % 3]:
                        st.image(url, use_container_width=True)

if __name__ == "__main__":
    main()

