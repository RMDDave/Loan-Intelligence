import pandas as pd
import streamlit as st
import os
from datetime import datetime
import uuid

# File to store loan applications
LOAN_APPLICATIONS_FILE = "loan_applications.csv"

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'username' not in st.session_state:
        st.session_state.username = None
    
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
        
    if 'temp_application' not in st.session_state:
        st.session_state.temp_application = {}
        
def create_applications_dataframe():
    """Initialize applications dataframe if it doesn't exist"""
    if not os.path.exists(LOAN_APPLICATIONS_FILE):
        df = pd.DataFrame(columns=[
            'application_id', 'applicant_username', 'applicant_name', 'email', 'phone',
            'loan_amount', 'loan_term', 'purpose', 'annual_income', 'employment_status',
            'employment_length', 'home_ownership', 'credit_score', 'monthly_debt',
            'application_date', 'status', 'model_score', 'officer_notes', 'decision_date',
            'decision_by'
        ])
        df.to_csv(LOAN_APPLICATIONS_FILE, index=False)
        return df
    return pd.read_csv(LOAN_APPLICATIONS_FILE)

def save_application(application_data):
    """Save a loan application to the CSV file"""
    # Create applications dataframe if it doesn't exist
    applications_df = create_applications_dataframe()
    
    # Generate a unique application ID
    application_id = str(uuid.uuid4())[:8]
    
    # Add current date and default status
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create application record
    application = {
        'application_id': application_id,
        'applicant_username': st.session_state.username,
        'applicant_name': application_data.get('full_name', ''),
        'email': application_data.get('email', ''),
        'phone': application_data.get('phone', ''),
        'loan_amount': application_data.get('loan_amount', 0),
        'loan_term': application_data.get('loan_term', 0),
        'purpose': application_data.get('purpose', ''),
        'annual_income': application_data.get('annual_income', 0),
        'employment_status': application_data.get('employment_status', ''),
        'employment_length': application_data.get('employment_length', 0),
        'home_ownership': application_data.get('home_ownership', ''),
        'credit_score': application_data.get('credit_score', 0),
        'monthly_debt': application_data.get('monthly_debt', 0),
        'application_date': current_date,
        'status': 'pending',
        'model_score': application_data.get('model_score', 0),
        'officer_notes': '',
        'decision_date': '',
        'decision_by': ''
    }
    
    # Append to existing applications
    updated_applications = pd.concat([applications_df, pd.DataFrame([application])], ignore_index=True)
    updated_applications.to_csv(LOAN_APPLICATIONS_FILE, index=False)
    
    return application_id

def load_user_applications(username):
    """Load all applications for a specific user"""
    if not os.path.exists(LOAN_APPLICATIONS_FILE):
        return pd.DataFrame()
    
    applications_df = pd.read_csv(LOAN_APPLICATIONS_FILE)
    
    if applications_df.empty:
        return pd.DataFrame()
    
    # Filter applications for the specific user
    user_applications = applications_df[applications_df['applicant_username'] == username]
    
    return user_applications

def load_application_by_id(application_id):
    """Load a specific application by its ID"""
    if not os.path.exists(LOAN_APPLICATIONS_FILE):
        return None
    
    applications_df = pd.read_csv(LOAN_APPLICATIONS_FILE)
    
    if applications_df.empty:
        return None
    
    # Find the application
    application = applications_df[applications_df['application_id'] == application_id]
    
    if application.empty:
        return None
    
    return application.iloc[0].to_dict()

def update_application_status(application_id, new_status, officer_username=None, notes=None):
    """Update the status of an application"""
    if not os.path.exists(LOAN_APPLICATIONS_FILE):
        return False
    
    applications_df = pd.read_csv(LOAN_APPLICATIONS_FILE)
    
    if applications_df.empty:
        return False
    
    # Find the application
    application_index = applications_df[applications_df['application_id'] == application_id].index
    
    if len(application_index) == 0:
        return False
    
    # Update status
    applications_df.loc[application_index, 'status'] = new_status
    
    # Update officer notes if provided
    if notes is not None:
        applications_df.loc[application_index, 'officer_notes'] = notes
    
    # Update decision details if this is a final decision
    if new_status in ['approved', 'rejected'] and officer_username:
        applications_df.loc[application_index, 'decision_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        applications_df.loc[application_index, 'decision_by'] = officer_username
    
    # Save updated dataframe
    applications_df.to_csv(LOAN_APPLICATIONS_FILE, index=False)
    
    return True

def get_loan_statistics():
    """Get statistics about loan applications"""
    if not os.path.exists(LOAN_APPLICATIONS_FILE):
        return {
            'total': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'average_amount': 0,
            'average_term': 0,
            'average_score': 0
        }
    
    applications_df = pd.read_csv(LOAN_APPLICATIONS_FILE)
    
    if applications_df.empty:
        return {
            'total': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'average_amount': 0,
            'average_term': 0,
            'average_score': 0
        }
    
    # Calculate statistics
    total = len(applications_df)
    pending = len(applications_df[applications_df['status'] == 'pending'])
    approved = len(applications_df[applications_df['status'] == 'approved'])
    rejected = len(applications_df[applications_df['status'] == 'rejected'])
    
    avg_amount = applications_df['loan_amount'].mean() if total > 0 else 0
    avg_term = applications_df['loan_term'].mean() if total > 0 else 0
    avg_score = applications_df['model_score'].mean() if total > 0 else 0
    
    return {
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'average_amount': avg_amount,
        'average_term': avg_term,
        'average_score': avg_score
    }
