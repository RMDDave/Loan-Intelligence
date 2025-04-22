import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """Validate phone number format"""
    # Remove common separators and check if it's a 10-digit number
    cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
    return bool(re.match(r'^\d{10}$', cleaned_phone))

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def calculate_monthly_payment(loan_amount, loan_term, interest_rate):
    """Calculate monthly loan payment"""
    if loan_term <= 0 or loan_amount <= 0:
        return 0
    
    # Convert annual interest rate to monthly and decimal
    monthly_rate = interest_rate / 100 / 12
    
    # Convert loan term from years to months
    loan_term_months = loan_term * 12
    
    # Calculate monthly payment using the loan formula
    if monthly_rate == 0:
        monthly_payment = loan_amount / loan_term_months
    else:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** loan_term_months) / ((1 + monthly_rate) ** loan_term_months - 1)
    
    return monthly_payment

def calculate_dti_ratio(monthly_debt, annual_income):
    """Calculate debt-to-income ratio"""
    if annual_income <= 0:
        return float('inf')
    
    monthly_income = annual_income / 12
    return monthly_debt / monthly_income

def generate_application_timeline(application_data):
    """Generate a timeline of application events"""
    events = []
    
    # Application submission
    if 'application_date' in application_data and application_data['application_date']:
        events.append({
            'date': pd.to_datetime(application_data['application_date']),
            'event': 'Application Submitted',
            'description': 'Your loan application was received.'
        })
    
    # Model scoring
    if 'model_score' in application_data and application_data['model_score'] > 0:
        # Assume scoring happened shortly after submission
        score_date = pd.to_datetime(application_data['application_date']) + timedelta(minutes=5)
        events.append({
            'date': score_date,
            'event': 'Initial Assessment',
            'description': f"Automated risk assessment completed with score: {application_data['model_score']}/100"
        })
    
    # Decision
    if 'decision_date' in application_data and application_data['decision_date']:
        decision = "approved" if application_data['status'] == 'approved' else "rejected"
        events.append({
            'date': pd.to_datetime(application_data['decision_date']),
            'event': f"Application {decision.capitalize()}",
            'description': f"Your application was {decision} by loan officer."
        })
    
    # Sort by date
    events = sorted(events, key=lambda x: x['date'])
    
    return events

def generate_loan_summary_figures(loan_data):
    """Generate summary figures for loan applications"""
    if not os.path.exists("loan_applications.csv"):
        return {}
    
    applications_df = pd.read_csv("loan_applications.csv")
    
    if applications_df.empty:
        return {}
    
    # Calculate figures
    figures = {}
    
    # Status distribution
    status_counts = applications_df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    figures['status_distribution'] = px.pie(
        status_counts, 
        values='Count', 
        names='Status', 
        title='Applications by Status',
        color_discrete_sequence=px.colors.sequential.Blues
    )
    
    # Loan amount distribution
    figures['loan_amount_distribution'] = px.histogram(
        applications_df, 
        x='loan_amount',
        nbins=10,
        title='Loan Amount Distribution',
        labels={'loan_amount': 'Loan Amount ($)', 'count': 'Number of Applications'},
        color_discrete_sequence=px.colors.sequential.Blues
    )
    
    # Loan term distribution
    term_counts = applications_df['loan_term'].value_counts().reset_index()
    term_counts.columns = ['Term (years)', 'Count']
    
    figures['loan_term_distribution'] = px.bar(
        term_counts,
        x='Term (years)',
        y='Count',
        title='Loan Term Distribution',
        color_discrete_sequence=px.colors.sequential.Blues
    )
    
    # Credit score vs. approval
    if 'credit_score' in applications_df.columns and not applications_df['credit_score'].isna().all():
        figures['credit_score_vs_approval'] = px.box(
            applications_df,
            x='status',
            y='credit_score',
            title='Credit Score by Application Status',
            labels={'status': 'Application Status', 'credit_score': 'Credit Score'},
            color='status',
            color_discrete_sequence=px.colors.sequential.Blues
        )
    
    # Application volume over time
    if 'application_date' in applications_df.columns:
        applications_df['application_date'] = pd.to_datetime(applications_df['application_date'])
        applications_df['application_day'] = applications_df['application_date'].dt.date
        
        daily_counts = applications_df.groupby('application_day').size().reset_index()
        daily_counts.columns = ['Date', 'Count']
        
        figures['application_volume'] = px.line(
            daily_counts,
            x='Date',
            y='Count',
            title='Application Volume Over Time',
            labels={'Date': 'Date', 'Count': 'Number of Applications'},
            markers=True
        )
    
    return figures
