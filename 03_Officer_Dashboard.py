import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from data import init_session_state, update_application_status, load_application_by_id
from utils import format_currency, calculate_dti_ratio
from ml_model import get_model_explanation

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="Loan Officer Dashboard",
    page_icon="👩‍💼",
    layout="wide"
)

# Check if user is authenticated
if not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Check if user is a loan officer
if st.session_state.user_type != "loan officer":
    st.error("This page is only accessible to loan officers.")
    st.stop()

# Main content
st.title("Loan Officer Dashboard")
st.write("Review and process loan applications.")

# Load all applications
LOAN_APPLICATIONS_FILE = "loan_applications.csv"
if os.path.exists(LOAN_APPLICATIONS_FILE):
    applications_df = pd.read_csv(LOAN_APPLICATIONS_FILE)
    
    if not applications_df.empty:
        # Convert dates to datetime for sorting
        applications_df['application_date'] = pd.to_datetime(applications_df['application_date'])
        
        # Dashboard summary
        col1, col2, col3, col4 = st.columns(4)
        
        # Total applications
        with col1:
            st.metric("Total Applications", len(applications_df))
        
        # Pending applications
        with col2:
            pending_count = applications_df[applications_df['status'] == 'pending'].shape[0]
            st.metric("Pending Applications", pending_count)
        
        # Approved applications
        with col3:
            approved_count = applications_df[applications_df['status'] == 'approved'].shape[0]
            approval_rate = approved_count / len(applications_df) * 100 if len(applications_df) > 0 else 0
            st.metric("Approved Applications", approved_count, f"{approval_rate:.1f}%")
        
        # Rejected applications
        with col4:
            rejected_count = applications_df[applications_df['status'] == 'rejected'].shape[0]
            st.metric("Rejected Applications", rejected_count)
        
        # Application view modes
        view_mode = st.radio("View", ["Pending Applications", "All Applications", "Application Details"], horizontal=True)
        
        if view_mode == "Pending Applications":
            # Filter for pending applications only
            pending_df = applications_df[applications_df['status'] == 'pending'].sort_values('application_date', ascending=False)
            
            if pending_df.empty:
                st.info("No pending applications to review.")
            else:
                st.subheader("Pending Applications")
                
                # Create a simplified view for the table
                display_df = pending_df[[
                    'application_id', 'applicant_name', 'loan_amount', 'loan_term', 
                    'application_date', 'model_score'
                ]].copy()
                
                # Format columns for display
                display_df['loan_amount'] = display_df['loan_amount'].apply(lambda x: format_currency(x))
                display_df['loan_term'] = display_df['loan_term'].apply(lambda x: f"{x} years")
                display_df['application_date'] = display_df['application_date'].dt.strftime('%Y-%m-%d')
                
                # Rename columns for better display
                display_df.columns = ['Application ID', 'Applicant', 'Loan Amount', 'Term', 'Date', 'Score']
                
                # Color code the score column based on value
                def color_score(val):
                    if pd.isna(val):
                        return ''
                    score = float(val)
                    if score >= 80:
                        return 'background-color: #d4edda'  # Light green for high scores
                    elif score >= 60:
                        return 'background-color: #fff3cd'  # Light yellow for medium scores
                    else:
                        return 'background-color: #f8d7da'  # Light red for low scores
                
                # Display the styled table
                st.dataframe(display_df.style.applymap(color_score, subset=['Score']), use_container_width=True)
                
                # Select application for review
                selected_id = st.selectbox("Select an application to review:", pending_df['application_id'].tolist())
                
                if selected_id:
                    # Load the selected application details
                    application = pending_df[pending_df['application_id'] == selected_id].iloc[0]
                    
                    st.divider()
                    st.subheader(f"Review Application: {selected_id}")
                    
                    # Display application details in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Applicant Information**")
                        st.write(f"Name: {application['applicant_name']}")
                        st.write(f"Email: {application['email']}")
                        st.write(f"Phone: {application['phone']}")
                        
                        st.write("**Loan Details**")
                        st.write(f"Amount: {format_currency(application['loan_amount'])}")
                        st.write(f"Term: {application['loan_term']} years")
                        st.write(f"Purpose: {application['purpose']}")
                        st.write(f"Application Date: {application['application_date'].strftime('%Y-%m-%d')}")
                    
                    with col2:
                        st.write("**Financial Information**")
                        st.write(f"Annual Income: {format_currency(application['annual_income'])}")
                        st.write(f"Employment Status: {application['employment_status']}")
                        st.write(f"Employment Length: {application['employment_length']} years")
                        st.write(f"Credit Score: {application['credit_score']}")
                        st.write(f"Monthly Debt: {format_currency(application['monthly_debt'])}")
                        
                        # Calculate and display DTI ratio
                        dti_ratio = calculate_dti_ratio(application['monthly_debt'], application['annual_income']) * 100
                        st.write(f"Debt-to-Income Ratio: {dti_ratio:.1f}%")
                        
                        if dti_ratio > 43:
                            st.warning("DTI ratio exceeds 43% threshold")
                    
                    # Display model score
                    st.subheader("Automated Assessment")
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        model_score = application['model_score']
                        if model_score >= 80:
                            st.success(f"Score: {model_score}/100")
                        elif model_score >= 60:
                            st.info(f"Score: {model_score}/100")
                        else:
                            st.warning(f"Score: {model_score}/100")
                    
                    with col2:
                        # Get explanation for the score
                        app_dict = application.to_dict()
                        explanations = get_model_explanation(app_dict)
                        for explanation in explanations:
                            st.write(f"• {explanation}")
                    
                    # Officer decision
                    st.subheader("Decision")
                    
                    decision_notes = st.text_area("Notes", placeholder="Enter your notes or comments about this application...")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve Application", key="approve_btn"):
                            if update_application_status(selected_id, "approved", st.session_state.username, decision_notes):
                                st.success("Application approved successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update application status.")
                    
                    with col2:
                        if st.button("Reject Application", key="reject_btn"):
                            if update_application_status(selected_id, "rejected", st.session_state.username, decision_notes):
                                st.success("Application rejected successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update application status.")
        
        elif view_mode == "All Applications":
            # Show all applications
            st.subheader("All Applications")
            
            # Sort by application date (most recent first)
            sorted_df = applications_df.sort_values('application_date', ascending=False)
            
            # Create a simplified view for the table
            display_df = sorted_df[[
                'application_id', 'applicant_name', 'loan_amount', 'loan_term', 
                'application_date', 'status', 'model_score'
            ]].copy()
            
            # Format columns for display
            display_df['loan_amount'] = display_df['loan_amount'].apply(lambda x: format_currency(x))
            display_df['loan_term'] = display_df['loan_term'].apply(lambda x: f"{x} years")
            display_df['application_date'] = display_df['application_date'].dt.strftime('%Y-%m-%d')
            display_df['status'] = display_df['status'].str.capitalize()
            
            # Rename columns for better display
            display_df.columns = ['Application ID', 'Applicant', 'Loan Amount', 'Term', 'Date', 'Status', 'Score']
            
            # Show full table
            st.dataframe(display_df, use_container_width=True)
            
            # Show applications by status chart
            st.subheader("Applications by Status")
            
            status_counts = applications_df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            
            fig = px.pie(
                status_counts, 
                values='Count', 
                names='Status', 
                title='Applications by Status',
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig, use_container_width=True)
        
        elif view_mode == "Application Details":
            # Application details view
            st.subheader("Application Details")
            
            # Application selector
            application_ids = applications_df['application_id'].tolist()
            selected_application_id = st.selectbox("Select an application:", application_ids)
            
            # Load selected application details
            application_details = load_application_by_id(selected_application_id)
            
            if application_details:
                # Show full application details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Applicant Information**")
                    st.write(f"Name: {application_details.get('applicant_name', '')}")
                    st.write(f"Username: {application_details.get('applicant_username', '')}")
                    st.write(f"Email: {application_details.get('email', '')}")
                    st.write(f"Phone: {application_details.get('phone', '')}")
                    
                    st.write("**Loan Details**")
                    st.write(f"Amount: {format_currency(application_details.get('loan_amount', 0))}")
                    st.write(f"Term: {application_details.get('loan_term', 0)} years")
                    st.write(f"Purpose: {application_details.get('purpose', '')}")
                    st.write(f"Application Date: {pd.to_datetime(application_details.get('application_date', '')).strftime('%Y-%m-%d')}")
                
                with col2:
                    st.write("**Financial Information**")
                    st.write(f"Annual Income: {format_currency(application_details.get('annual_income', 0))}")
                    st.write(f"Employment Status: {application_details.get('employment_status', '')}")
                    st.write(f"Employment Length: {application_details.get('employment_length', 0)} years")
                    st.write(f"Home Ownership: {application_details.get('home_ownership', '')}")
                    st.write(f"Credit Score: {application_details.get('credit_score', 0)}")
                    st.write(f"Monthly Debt: {format_currency(application_details.get('monthly_debt', 0))}")
                    
                    # Calculate and display DTI ratio
                    annual_income = application_details.get('annual_income', 0)
                    monthly_debt = application_details.get('monthly_debt', 0)
                    if annual_income > 0:
                        monthly_income = annual_income / 12
                        dti_ratio = (monthly_debt / monthly_income) * 100
                        st.write(f"Debt-to-Income Ratio: {dti_ratio:.1f}%")
                
                # Application status and decision information
                st.divider()
                st.subheader("Application Status")
                
                status = application_details.get('status', 'unknown')
                if status == 'approved':
                    st.success("Approved")
                elif status == 'rejected':
                    st.error("Rejected")
                elif status == 'pending':
                    st.info("Pending Review")
                else:
                    st.warning(status.capitalize())
                
                # Display decision details if available
                if application_details.get('decision_date', ''):
                    st.write(f"Decision Date: {application_details.get('decision_date', '')}")
                    st.write(f"Decision By: {application_details.get('decision_by', '')}")
                
                if application_details.get('officer_notes', ''):
                    st.write("Officer Notes:")
                    st.write(application_details.get('officer_notes', ''))
                
                # Show model score
                if 'model_score' in application_details and application_details['model_score'] > 0:
                    st.divider()
                    st.subheader("Model Assessment")
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        model_score = application_details['model_score']
                        if model_score >= 80:
                            st.success(f"Score: {model_score}/100")
                        elif model_score >= 60:
                            st.info(f"Score: {model_score}/100")
                        else:
                            st.warning(f"Score: {model_score}/100")
                    
                    with col2:
                        # Get explanation for the score
                        explanations = get_model_explanation(application_details)
                        for explanation in explanations:
                            st.write(f"• {explanation}")
                
                # Only show decision buttons for pending applications
                if status == 'pending':
                    st.divider()
                    st.subheader("Update Decision")
                    
                    decision_notes = st.text_area("Notes", placeholder="Enter your notes or comments...", key="update_notes")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Approve Application"):
                            if update_application_status(selected_application_id, "approved", st.session_state.username, decision_notes):
                                st.success("Application approved successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update application status.")
                    
                    with col2:
                        if st.button("Reject Application"):
                            if update_application_status(selected_application_id, "rejected", st.session_state.username, decision_notes):
                                st.success("Application rejected successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update application status.")
    else:
        st.info("No applications have been submitted yet.")
else:
    st.info("No applications have been submitted yet.")
