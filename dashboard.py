# coba.py

import streamlit as st
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

@st.cache_data
def load_data(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        st.error(f"File data '{json_path}' tidak ditemukan.")
        return pd.DataFrame()

    # Menggunakan iterasi manual untuk penanganan data yang lebih aman
    records = []
    for item in data:
        record = {
            'text': item.get('text', ''),
            'FROM': item.get('entities', {}).get('FROM'),
            'TO': item.get('entities', {}).get('TO'),
            'STATUS': item.get('entities', {}).get('STATUS'),
            'OBSTACLE': item.get('entities', {}).get('OBSTACLE'),
            'DATE': item.get('entities', {}).get('DATE'),
            'TIME': item.get('entities', {}).get('TIME')
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Konversi tipe data
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y', errors='coerce')
        df.dropna(subset=['DATE'], inplace=True)
    
    if 'TIME' in df.columns:
        df['HOUR'] = pd.to_datetime(df['TIME'], format='%H:%M', errors='coerce').dt.hour

    return df

st.set_page_config(layout="wide")
st.title("🚦 Dashboard Analisis Laporan Lalu Lintas")

df = load_data('hasil_ekstraksi_final_split.json')

if not df.empty:
    st.sidebar.header("Filter Data")
    
    if 'DATE' in df.columns and not df['DATE'].empty:
        min_date = df['DATE'].min()
        max_date = df['DATE'].max()

        date_range = st.sidebar.date_input(
            "Pilih Rentang Tanggal:", value=(min_date, max_date),
            min_value=min_date, max_value=max_date, format="DD/MM/YYYY"
        )

        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df[(df['DATE'].dt.date >= start_date) & (df['DATE'].dt.date <= end_date)]
        else:
            df_filtered = df.copy()
    else:
        df_filtered = df.copy()

    st.subheader("Ringkasan Laporan")
    col1, col2 = st.columns(2)
    total_laporan = len(df_filtered)
    total_obstacle = df_filtered['OBSTACLE'].notna().sum()
    
    col1.metric("Total Laporan", f"{total_laporan}")
    col2.metric("Total Laporan Obstacle", f"{total_obstacle}")

    st.markdown("---")

    # --- Layout Visualisasi 2x2 ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Frekuensi Laporan per Jam")
        if 'HOUR' in df_filtered.columns and not df_filtered['HOUR'].dropna().empty:
            hourly_reports = df_filtered['HOUR'].value_counts().sort_index()
            fig_hourly = px.bar(
                x=hourly_reports.index,
                y=hourly_reports.values,
                labels={'x': 'Jam', 'y': 'Jumlah Laporan'},
                text_auto=True
            )
            fig_hourly.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("Tidak ada data jam untuk ditampilkan.")

    with col_chart2:
        st.subheader("Distribusi Status Lalin")
        if not df_filtered['STATUS'].dropna().empty:
            status_counts = df_filtered['STATUS'].value_counts()
            fig_pie = px.pie(
                status_counts, 
                values=status_counts.values, 
                names=status_counts.index, 
                hole=0.3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Tidak ada data status untuk ditampilkan.")

    st.markdown("---")
    
    col_chart3, col_chart4 = st.columns(2)

    # --- VISUALISASI BARU: Penyebab Kemacetan ---
    with col_chart3:
        st.subheader("Penyebab Kemacetan")
        if not df_filtered['OBSTACLE'].dropna().empty:
            # Explode list di kolom OBSTACLE untuk menghitung setiap kejadian
            obstacles = df_filtered.dropna(subset=['OBSTACLE'])['OBSTACLE'].explode().value_counts()
            fig_obstacle = px.bar(
                obstacles, 
                x=obstacles.index, 
                y=obstacles.values,
                labels={'x': 'Jenis Penyebab', 'y': 'Jumlah'},
                text_auto=True
            )
            st.plotly_chart(fig_obstacle, use_container_width=True)
        else:
            st.info("Tidak ada data penyebab kemacetan untuk ditampilkan.")

    with col_chart4:
        st.subheader("Top 5 Lokasi Asal Laporan")
        if not df_filtered['FROM'].dropna().empty:
            top_5_from = df_filtered['FROM'].value_counts().head(5)
            fig_from = px.bar(
                top_5_from, 
                y=top_5_from.index, 
                x=top_5_from.values, 
                orientation='h',
                labels={'y': 'Lokasi', 'x': 'Jumlah Laporan'}
            )
            fig_from.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_from, use_container_width=True)
        else:
            st.info("Tidak ada data lokasi asal untuk ditampilkan.")
else:
    st.warning("Data tidak dapat dimuat atau kosong.")