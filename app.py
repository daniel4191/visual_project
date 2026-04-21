import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 대시보드 기본 설정
st.set_page_config(page_title="브라질 Olist 이커머스 대시보드", layout="wide")

# 고정 환율 설정 (1 BRL = 260 KRW)
EXCHANGE_RATE = 260

# 2. 데이터 로드 및 병합 (캐싱 적용)
@st.cache_data
def load_data():
    orders = pd.read_csv('./data/olist_orders_dataset.csv')
    items = pd.read_csv('./data/olist_order_items_dataset.csv')
    customers = pd.read_csv('./data/olist_customers_dataset.csv')
    products = pd.read_csv('./data/olist_products_dataset.csv')
    translations = pd.read_csv('./data/product_category_name_translation.csv')

    orders = orders[orders['order_status'] == 'delivered']

    df = pd.merge(orders, items, on='order_id', how='inner')
    df = pd.merge(df, customers, on='customer_id', how='inner')
    df = pd.merge(df, products, on='product_id', how='left')
    df = pd.merge(df, translations, on='product_category_name', how='left')

    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['YearMonth'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    
    return df

with st.spinner('📦 데이터를 분석 중입니다...'):
    df = load_data()

# 3. 사이드바 필터
st.sidebar.header("데이터 필터링")

df['Year'] = df['order_purchase_timestamp'].dt.year
selected_year = st.sidebar.multiselect("연도 선택", options=sorted(df['Year'].unique()), default=sorted(df['Year'].unique()))

selected_state = st.sidebar.multiselect("주(State) 선택", options=sorted(df['customer_state'].unique()), default=['SP', 'RJ', 'MG'])

filtered_df = df[(df['Year'].isin(selected_year)) & (df['customer_state'].isin(selected_state))]

# 4. 메인 화면 KPI
st.title("이커머스 비즈니스 통합 대시보드")
st.markdown("**Python, Pandas, Plotly**를 활용하여 5개의 테이블을 병합한 실시간 대시보드입니다.")
st.markdown(f"*(환율 기준: 1 BRL = {EXCHANGE_RATE} KRW)*")
st.markdown("---")

# 지표 계산
total_rev_brl = filtered_df['price'].sum() + filtered_df['freight_value'].sum()
total_rev_krw = total_rev_brl * EXCHANGE_RATE

total_orders = filtered_df['order_id'].nunique()
unique_customers = filtered_df['customer_unique_id'].nunique()

aov_brl = total_rev_brl / total_orders if total_orders > 0 else 0
aov_krw = aov_brl * EXCHANGE_RATE

col1, col2, col3, col4 = st.columns(4)

# ★ BRL 메인, KRW 서브 표시 (이 부분이 바뀌었습니다!)
col1.metric(label="누적 매출액 (BRL)", value=f"R$ {total_rev_brl:,.0f}", help=f"원화 환산: ₩ {total_rev_krw:,.0f}")
col1.caption(f"**₩ {total_rev_krw:,.0f}**")

col2.metric(label="총 주문 건수", value=f"{total_orders:,.0f} 건")

col3.metric(label="객단가 (AOV: Average Order Value)", value=f"R$ {aov_brl:,.0f}", help=f"원화 환산: ₩ {aov_krw:,.0f}")
col3.caption(f"**₩ {aov_krw:,.0f}**")

col4.metric(label="구매 고객 수", value=f"{unique_customers:,.0f} 명")

st.markdown("---")

# 5. 시각화 차트
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("월별 매출 트렌드 (BRL)")
    trend_df = filtered_df.groupby('YearMonth')['price'].sum().reset_index()
    fig_trend = px.line(trend_df, x='YearMonth', y='price', markers=True, 
                        line_shape='spline', color_discrete_sequence=['#1f77b4'])
    fig_trend.update_layout(xaxis_title="월", yaxis_title="매출액 (R$)")
    st.plotly_chart(fig_trend, use_container_width=True)

with col_chart2:
    st.subheader("Top 10 판매 카테고리")
    cat_df = filtered_df.groupby('product_category_name_english')['price'].sum().reset_index()
    cat_df = cat_df.sort_values(by='price', ascending=False).head(10)
    fig_cat = px.bar(cat_df, x='price', y='product_category_name_english', orientation='h', 
                     color='price', color_continuous_scale='Blues')
    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="매출액 (R$)", yaxis_title="카테고리")
    st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("---")

col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("주(State)별 매출 비중")
    state_df = filtered_df.groupby('customer_state')['price'].sum().reset_index()
    fig_state = px.pie(state_df, values='price', names='customer_state', hole=0.4,
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_state.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_state, use_container_width=True)

with col_chart4:
    st.subheader("배송비(Freight) vs 상품가격(Price) 분포")
    sample_df = filtered_df.sample(n=min(5000, len(filtered_df)), random_state=42)
    fig_scatter = px.scatter(sample_df, x='price', y='freight_value', color='customer_state',
                             opacity=0.6, hover_data=['product_category_name_english'])
    fig_scatter.update_layout(xaxis_title="상품 가격 (R$)", yaxis_title="배송비 (R$)")
    st.plotly_chart(fig_scatter, use_container_width=True)