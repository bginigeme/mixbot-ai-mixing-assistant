#!/usr/bin/env python3
"""
Mixbot Analytics Dashboard
Simple dashboard to view user analytics data
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def load_analytics_data():
    """Load analytics data from JSONL file"""
    try:
        data = []
        with open("user_analytics.jsonl", "r") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    except FileNotFoundError:
        return []

def create_analytics_dashboard():
    """Create the analytics dashboard"""
    st.set_page_config(page_title="Mixbot Analytics", page_icon="📊", layout="wide")
    
    st.title("📊 Mixbot Analytics Dashboard")
    st.markdown("---")
    
    # Load data
    data = load_analytics_data()
    
    if not data:
        st.warning("No analytics data found. Start using the app to generate data!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    df_recent = df[df['timestamp'] > thirty_days_ago]
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", len(df['session_id'].unique()))
    
    with col2:
        st.metric("Total Actions", len(df))
    
    with col3:
        st.metric("File Uploads", len(df[df['action'] == 'file_upload']))
    
    with col4:
        st.metric("Analyses Completed", len(df[df['action'] == 'analysis_complete']))
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Actions Over Time")
        daily_actions = df_recent.groupby(df_recent['timestamp'].dt.date)['action'].count().reset_index()
        daily_actions.columns = ['date', 'count']
        
        fig = px.line(daily_actions, x='date', y='count', title="Daily User Actions")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎛️ DAW Usage")
        daw_data = df[df['action'] == 'daw_selection']
        if not daw_data.empty:
            daw_counts = daw_data['details'].apply(lambda x: x.get('daw', 'Unknown') if x else 'Unknown').value_counts()
            fig = px.pie(values=daw_counts.values, names=daw_counts.index, title="Most Popular DAWs")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No DAW selection data yet")
    
    # Genre analysis
    st.subheader("🎵 Genre Distribution")
    genre_data = df[df['action'] == 'genre_detection']
    if not genre_data.empty:
        genre_counts = genre_data['details'].apply(lambda x: x.get('genre', 'Unknown') if x else 'Unknown').value_counts()
        fig = px.bar(x=genre_counts.index, y=genre_counts.values, title="Detected Genres")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No genre detection data yet")
    
    # File type analysis
    st.subheader("📁 File Types")
    file_data = df[df['action'] == 'file_upload']
    if not file_data.empty:
        file_types = file_data['details'].apply(lambda x: x.get('file_type', 'Unknown') if x else 'Unknown').value_counts()
        fig = px.pie(values=file_types.values, names=file_types.index, title="Uploaded File Types")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No file upload data yet")
    
    # Analysis performance
    st.subheader("⚡ Analysis Performance")
    analysis_data = df[df['action'] == 'analysis_complete']
    if not analysis_data.empty:
        analysis_times = [d.get('analysis_time_seconds', 0) for d in analysis_data['details'] if d]
        if analysis_times:
            avg_time = sum(analysis_times) / len(analysis_times)
            st.metric("Average Analysis Time", f"{avg_time:.2f} seconds")
            
            fig = px.histogram(x=analysis_times, title="Analysis Time Distribution", 
                             labels={'x': 'Time (seconds)', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Raw data
    with st.expander("📋 Raw Analytics Data"):
        st.dataframe(df)

if __name__ == "__main__":
    create_analytics_dashboard() 