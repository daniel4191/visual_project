import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("Olist 이커머스 주문 현황 대시보드")

# 데이터 불러오기
file_path = './data/olist_orders_dataset.csv'
df = pd.read_csv(file_path)

# 주문 상태별 카운트 계산
status_count = df['order_status'].value_counts().reset_index()
status_count.columns = ['Status', 'Count']

st.subheader("📌 주문 상태별 비율")

# Plotly를 이용한 세련된 파이 차트 생성
fig = px.pie(status_count, values='Count', names='Status', 
             title='Order Status Distribution', hole=0.4)

# Streamlit 화면에 차트 출력
st.plotly_chart(fig, use_container_width=True)