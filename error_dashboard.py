#!/usr/bin/env python3
"""
Mixbot Error Dashboard
Dashboard to view and analyze error logs from Mixbot
"""
import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def load_error_data():
    """Load error data from error_log.jsonl"""
    errors = []
    try:
        with open("error_log.jsonl", "r") as f:
            for line in f:
                try:
                    error_data = json.loads(line.strip())
                    errors.append(error_data)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        st.warning("No error log file found. Errors will appear here once they occur.")
        return pd.DataFrame()
    
    if not errors:
        st.success("🎉 No errors logged! Your app is running smoothly.")
        return pd.DataFrame()
    
    return pd.DataFrame(errors)

def create_error_dashboard():
    """Create the error dashboard"""
    st.set_page_config(
        page_title="Mixbot Error Dashboard",
        page_icon="🚨",
        layout="wide"
    )
    
    st.title("🚨 Mixbot Error Dashboard")
    st.markdown("Monitor and analyze errors from your Mixbot application")
    
    # Load error data
    df = load_error_data()
    
    if df.empty:
        return
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(df['date'].min(), df['date'].max()),
        min_value=df['date'].min(),
        max_value=df['date'].max()
    )
    
    # Error type filter
    error_types = ['All'] + list(df['error_type'].unique())
    selected_error_type = st.sidebar.selectbox("Error Type", error_types)
    
    # User context filter
    contexts = ['All'] + list(df['user_context'].dropna().unique())
    selected_context = st.sidebar.selectbox("User Context", contexts)
    
    # Apply filters
    filtered_df = df.copy()
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['date'] >= date_range[0]) & 
            (filtered_df['date'] <= date_range[1])
        ]
    
    if selected_error_type != 'All':
        filtered_df = filtered_df[filtered_df['error_type'] == selected_error_type]
    
    if selected_context != 'All':
        filtered_df = filtered_df[filtered_df['user_context'] == selected_context]
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Errors", len(filtered_df))
    
    with col2:
        st.metric("Unique Error Types", filtered_df['error_type'].nunique())
    
    with col3:
        st.metric("Affected Sessions", filtered_df['session_id'].nunique())
    
    with col4:
        if len(filtered_df) > 0:
            recent_errors = filtered_df[filtered_df['timestamp'] > datetime.now() - timedelta(hours=24)]
            st.metric("Last 24h Errors", len(recent_errors))
        else:
            st.metric("Last 24h Errors", 0)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Errors by Type")
        error_counts = filtered_df['error_type'].value_counts()
        fig_errors = px.bar(
            x=error_counts.index, 
            y=error_counts.values,
            title="Error Type Distribution"
        )
        fig_errors.update_layout(xaxis_title="Error Type", yaxis_title="Count")
        st.plotly_chart(fig_errors, use_container_width=True)
    
    with col2:
        st.subheader("📈 Errors Over Time")
        daily_errors = filtered_df.groupby('date').size().reset_index(name='count')
        fig_timeline = px.line(
            daily_errors, 
            x='date', 
            y='count',
            title="Daily Error Count"
        )
        fig_timeline.update_layout(xaxis_title="Date", yaxis_title="Error Count")
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Error details table
    st.subheader("🔍 Error Details")
    
    # Create a more readable table
    display_df = filtered_df[['timestamp', 'error_type', 'error_message', 'user_context', 'session_id']].copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['error_message'] = display_df['error_message'].str[:100] + '...'  # Truncate long messages
    
    # Rename columns for display
    display_df.columns = ['Timestamp', 'Error Type', 'Error Message', 'Context', 'Session ID']
    
    st.dataframe(display_df, use_container_width=True)
    
    # Detailed error view
    if len(filtered_df) > 0:
        st.subheader("📋 Detailed Error Information")
        
        selected_error = st.selectbox(
            "Select an error to view details:",
            range(len(filtered_df)),
            format_func=lambda x: f"{filtered_df.iloc[x]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {filtered_df.iloc[x]['error_type']}"
        )
        
        if selected_error is not None:
            error = filtered_df.iloc[selected_error]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Error Information:**")
                st.json({
                    "Timestamp": error['timestamp'].isoformat(),
                    "Error Type": error['error_type'],
                    "Error Message": error['error_message'],
                    "User Context": error['user_context'],
                    "Session ID": error['session_id']
                })
            
            with col2:
                st.markdown("**Error Details:**")
                if error['error_details']:
                    st.json(error['error_details'])
                else:
                    st.info("No additional details available")
    
    # Error patterns and insights
    st.subheader("💡 Error Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Most Common Error Types:**")
        top_errors = filtered_df['error_type'].value_counts().head(5)
        for error_type, count in top_errors.items():
            st.markdown(f"- **{error_type}**: {count} occurrences")
    
    with col2:
        st.markdown("**Error Contexts:**")
        context_counts = filtered_df['user_context'].value_counts()
        for context, count in context_counts.items():
            if pd.notna(context):
                st.markdown(f"- **{context}**: {count} errors")
    
    # Recommendations
    st.subheader("🛠️ Recommendations")
    
    if len(filtered_df) > 0:
        # Analyze error patterns
        file_errors = filtered_df[filtered_df['error_type'].str.contains('file', case=False)]
        analysis_errors = filtered_df[filtered_df['error_type'].str.contains('analysis', case=False)]
        ui_errors = filtered_df[filtered_df['error_type'].str.contains('ui', case=False)]
        
        if len(file_errors) > 0:
            st.warning("**File Processing Issues Detected:**")
            st.markdown("- Consider adding file validation")
            st.markdown("- Check file size limits")
            st.markdown("- Verify supported file formats")
        
        if len(analysis_errors) > 0:
            st.warning("**Analysis Issues Detected:**")
            st.markdown("- Review audio processing pipeline")
            st.markdown("- Check librosa/soundfile dependencies")
            st.markdown("- Consider adding fallback analysis methods")
        
        if len(ui_errors) > 0:
            st.warning("**UI Issues Detected:**")
            st.markdown("- Review Streamlit component interactions")
            st.markdown("- Check session state management")
            st.markdown("- Verify responsive design on mobile")
    else:
        st.success("🎉 No errors to analyze! Your app is running smoothly.")

if __name__ == "__main__":
    create_error_dashboard() 