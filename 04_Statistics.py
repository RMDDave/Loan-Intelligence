import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from data import init_session_state, get_loan_statistics
from utils import generate_loan_summary_figures

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="Loan Statistics",
    page_icon="📊",
    layout="wide"
)

# Check if user is authenticated
if not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Main content
st.title("Loan Statistics and Analytics")

# Get statistics
stats = get_loan_statistics()

# Create summary cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Applications", stats['total'])

with col2:
    approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
    st.metric("Approval Rate", f"{approval_rate:.1f}%")

with col3:
    avg_amount = stats['average_amount']
    st.metric("Average Loan Amount", f"${avg_amount:,.2f}")

with col4:
    avg_term = stats['average_term']
    st.metric("Average Loan Term", f"{avg_term:.1f} years")

# Check if we have data
if stats['total'] == 0:
    st.info("Not enough data to generate statistics. Application statistics will appear here as more loans are processed.")
    st.stop()

# Load data for visualizations
if os.path.exists("loan_applications.csv"):
    df = pd.read_csv("loan_applications.csv")
    
    if not df.empty:
        # Convert date columns to datetime
        df['application_date'] = pd.to_datetime(df['application_date'])
        if 'decision_date' in df.columns:
            df['decision_date'] = pd.to_datetime(df['decision_date'])
        
        # Create tabs for different statistics
        tab1, tab2, tab3 = st.tabs(["Application Overview", "Financial Analysis", "Time Series"])
        
        # Tab 1: Application Overview
        with tab1:
            st.subheader("Application Status Distribution")
            
            # Status distribution chart
            status_counts = df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig1 = px.pie(
                status_counts, 
                values='Count', 
                names='Status', 
                title='Applications by Status',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Loan purpose distribution
            st.subheader("Loan Purpose Distribution")
            
            purpose_counts = df['purpose'].value_counts().reset_index()
            purpose_counts.columns = ['Purpose', 'Count']
            
            fig2 = px.bar(
                purpose_counts,
                x='Purpose',
                y='Count',
                title='Applications by Loan Purpose',
                color='Count',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Approval rate by purpose
            st.subheader("Approval Rate by Purpose")
            
            # Calculate approval rates
            purpose_approval = df.groupby('purpose')['status'].apply(
                lambda x: (x == 'approved').sum() / len(x) * 100 if len(x) > 0 else 0
            ).reset_index()
            purpose_approval.columns = ['Purpose', 'Approval Rate (%)']
            
            fig3 = px.bar(
                purpose_approval,
                x='Purpose',
                y='Approval Rate (%)',
                title='Approval Rate by Loan Purpose',
                color='Approval Rate (%)',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        # Tab 2: Financial Analysis
        with tab2:
            st.subheader("Loan Amount Distribution")
            
            # Loan amount histogram
            fig4 = px.histogram(
                df,
                x='loan_amount',
                nbins=20,
                title='Loan Amount Distribution',
                labels={'loan_amount': 'Loan Amount ($)', 'count': 'Number of Applications'},
                color_discrete_sequence=['#1E88E5']
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Credit score vs. approval
            st.subheader("Credit Score vs. Application Status")
            
            fig5 = px.box(
                df,
                x='status',
                y='credit_score',
                title='Credit Score by Application Status',
                labels={'status': 'Application Status', 'credit_score': 'Credit Score'},
                color='status',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig5, use_container_width=True)
            
            # Income vs. loan amount
            st.subheader("Income vs. Loan Amount")
            
            fig6 = px.scatter(
                df,
                x='annual_income',
                y='loan_amount',
                color='status',
                size='credit_score',
                hover_name='applicant_name',
                title='Annual Income vs. Loan Amount',
                labels={
                    'annual_income': 'Annual Income ($)',
                    'loan_amount': 'Loan Amount ($)',
                    'credit_score': 'Credit Score'
                },
                color_discrete_sequence=px.colors.qualitative.Set1
            )
            st.plotly_chart(fig6, use_container_width=True)
            
            # Add a trendline
            df_approved = df[df['status'] == 'approved']
            if not df_approved.empty:
                z = np.polyfit(df_approved['annual_income'], df_approved['loan_amount'], 1)
                p = np.poly1d(z)
                
                # Add trendline to the plot
                x_range = np.linspace(df['annual_income'].min(), df['annual_income'].max(), 100)
                fig6.add_trace(go.Scatter(
                    x=x_range,
                    y=p(x_range),
                    mode='lines',
                    name='Trend (Approved)',
                    line=dict(color='green', dash='dash')
                ))
                
                st.plotly_chart(fig6, use_container_width=True)
        
        # Tab 3: Time Series
        with tab3:
            st.subheader("Application Volume Over Time")
            
            # Group by date to get daily counts
            df['application_day'] = df['application_date'].dt.date
            daily_counts = df.groupby('application_day').size().reset_index()
            daily_counts.columns = ['Date', 'Count']
            
            fig7 = px.line(
                daily_counts,
                x='Date',
                y='Count',
                title='Daily Application Volume',
                labels={'Date': 'Date', 'Count': 'Number of Applications'},
                markers=True
            )
            st.plotly_chart(fig7, use_container_width=True)
            
            # Approval rate over time
            st.subheader("Approval Rate Over Time")
            
            # Calculate approval rate by week
            df['application_week'] = df['application_date'].dt.to_period('W').astype(str)
            weekly_approval = df.groupby('application_week').apply(
                lambda x: (x['status'] == 'approved').sum() / len(x) * 100 if len(x) > 0 else 0
            ).reset_index()
            weekly_approval.columns = ['Week', 'Approval Rate (%)']
            
            fig8 = px.line(
                weekly_approval,
                x='Week',
                y='Approval Rate (%)',
                title='Weekly Approval Rate',
                labels={'Week': 'Week', 'Approval Rate (%)': 'Approval Rate (%)'},
                markers=True
            )
            st.plotly_chart(fig8, use_container_width=True)
            
            # Processing time analysis (if decision dates are available)
            if 'decision_date' in df.columns and not df['decision_date'].isna().all():
                st.subheader("Application Processing Time")
                
                # Calculate processing time
                df_decided = df.dropna(subset=['decision_date'])
                df_decided['processing_time'] = (df_decided['decision_date'] - df_decided['application_date']).dt.total_seconds() / (60 * 60 * 24)  # in days
                
                fig9 = px.histogram(
                    df_decided,
                    x='processing_time',
                    nbins=10,
                    title='Application Processing Time (Days)',
                    labels={'processing_time': 'Processing Time (Days)', 'count': 'Number of Applications'},
                    color='status',
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                st.plotly_chart(fig9, use_container_width=True)
                
                # Average processing time by purpose
                avg_time_by_purpose = df_decided.groupby('purpose')['processing_time'].mean().reset_index()
                avg_time_by_purpose.columns = ['Purpose', 'Average Processing Time (Days)']
                
                fig10 = px.bar(
                    avg_time_by_purpose,
                    x='Purpose',
                    y='Average Processing Time (Days)',
                    title='Average Processing Time by Loan Purpose',
                    color='Average Processing Time (Days)',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig10, use_container_width=True)
    else:
        st.info("Not enough data to generate detailed statistics.")
else:
    st.info("No application data available yet.")
