import streamlit as st
import pandas as pd
import plotly.express as px
from auth import authenticate_user, create_user, is_loan_officer
from data import init_session_state, load_user_applications, save_application
import os

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="Loan Management System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar for login/logout
st.sidebar.title("Loan Management System")

# Authentication
if not st.session_state.authenticated:
    st.sidebar.header("Login")
    login_tab, signup_tab = st.sidebar.tabs(["Login", "Sign Up"])
    
    with login_tab:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        user_type = st.selectbox("User Type", ["Applicant", "Loan Officer"], key="login_type")
        
        if st.button("Login", key="login_button"):
            if authenticate_user(username, password, user_type.lower()):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.user_type = user_type.lower()
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")
    
    with signup_tab:
        new_username = st.text_input("Username", key="signup_username")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        new_user_type = st.selectbox("User Type", ["Applicant", "Loan Officer"], key="signup_type")
        
        if st.button("Sign Up", key="signup_button"):
            if new_password != confirm_password:
                st.sidebar.error("Passwords do not match")
            elif not new_username or not new_password:
                st.sidebar.error("Username and password cannot be empty")
            else:
                if create_user(new_username, new_password, new_user_type.lower()):
                    st.sidebar.success("Account created successfully! Please login.")
                else:
                    st.sidebar.error("Username already exists")

    # Main content for unauthenticated users
    st.title("Welcome to the Loan Management System")
    st.write("""
    This platform provides a comprehensive solution for loan management with AI-powered decision support.
    
    ### Features:
    - Easy online loan application
    - Real-time application status tracking
    - Intelligent loan approval system
    - Personalized loan offers
    
    Please login or create an account to continue.
    """)
    
    # Display a sample stats visualization for marketing purposes
    st.subheader("Our Performance")
    
    # Sample data for informational visualization
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Average Processing Time", value="24 hours")
    with col2:
        st.metric(label="Customer Satisfaction", value="4.8/5")
    with col3:
        st.metric(label="Approval Rate", value="73%")

else:
    # Show logout button if authenticated
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()
    
    st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
    st.sidebar.write(f"User type: **{st.session_state.user_type}**")
    
    # Main app page for authenticated users
    st.title("Loan Management Dashboard")
    
    if st.session_state.user_type == "applicant":
        st.write(f"Welcome {st.session_state.username}! You can apply for a loan or check your existing applications.")
        
        # Show quick stats for the applicant
        applications = load_user_applications(st.session_state.username)
        
        if not applications.empty:
            st.subheader("Your Loan Applications Summary")
            
            # Application counts by status
            status_counts = applications['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            col1, col2 = st.columns([2, 3])
            
            with col1:
                st.dataframe(status_counts)
            
            with col2:
                if len(status_counts) > 0:
                    fig = px.pie(status_counts, values='Count', names='Status', 
                                 title='Your Applications by Status',
                                 color_discrete_sequence=px.colors.sequential.Blues)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No application data to display")
        
    elif st.session_state.user_type == "loan officer":
        st.write(f"Welcome {st.session_state.username}! You can review loan applications and make decisions.")
        
        # Show quick stats for loan officers
        applications = pd.read_csv("loan_applications.csv") if os.path.exists("loan_applications.csv") else pd.DataFrame()
        
        if not applications.empty:
            # Count pending applications
            pending_count = len(applications[applications['status'] == 'pending'])
            
            # Calculate approval rate
            decided_apps = applications[applications['status'].isin(['approved', 'rejected'])]
            approval_rate = 0
            if len(decided_apps) > 0:
                approval_rate = len(decided_apps[decided_apps['status'] == 'approved']) / len(decided_apps) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Pending Applications", pending_count)
            
            with col2:
                st.metric("Approval Rate", f"{approval_rate:.1f}%")
            
            # Recent applications
            st.subheader("Recent Applications")
            st.dataframe(
                applications.sort_values('application_date', ascending=False)
                .head(5)[['application_id', 'applicant_name', 'loan_amount', 'status', 'application_date']]
            )
        else:
            st.info("No applications have been submitted yet.")
    
    st.write("Navigate to different sections using the pages in the sidebar.")
