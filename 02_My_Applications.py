import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from data import init_session_state, load_user_applications, load_application_by_id
from utils import format_currency, generate_application_timeline, calculate_monthly_payment

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="My Applications",
    page_icon="📋",
    layout="wide"
)

# Check if user is authenticated
if not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Check if user is an applicant
if st.session_state.user_type != "applicant":
    st.error("This page is only accessible to loan applicants.")
    st.stop()

# Main content
st.title("My Loan Applications")
st.write("View and track your loan applications.")

# Load user applications
applications = load_user_applications(st.session_state.username)

if applications.empty:
    st.info("You haven't submitted any loan applications yet.")
    
    # Add a button to create new application
    if st.button("Apply for a Loan"):
        st.switch_page("pages/01_Apply_for_Loan.py")
else:
    # Application summary counts
    status_counts = applications['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    # Create three columns for the summary metrics
    col1, col2, col3 = st.columns(3)
    
    # Total applications
    with col1:
        st.metric("Total Applications", len(applications))
    
    # Pending applications
    with col2:
        pending_count = applications[applications['status'] == 'pending'].shape[0]
        st.metric("Pending Applications", pending_count)
    
    # Approved applications
    with col3:
        approved_count = applications[applications['status'] == 'approved'].shape[0]
        st.metric("Approved Applications", approved_count)
    
    # Add a button to create new application
    if st.button("Apply for a New Loan"):
        st.switch_page("pages/01_Apply_for_Loan.py")
    
    # Applications list
    st.subheader("Application List")
    
    # Sort applications by date (most recent first)
    applications['application_date'] = pd.to_datetime(applications['application_date'])
    sorted_applications = applications.sort_values('application_date', ascending=False)
    
    # Create simple table view
    cols_to_display = ['application_id', 'loan_amount', 'loan_term', 'purpose', 'application_date', 'status']
    display_df = sorted_applications[cols_to_display].copy()
    
    # Format columns for display
    display_df['loan_amount'] = display_df['loan_amount'].apply(lambda x: format_currency(x))
    display_df['loan_term'] = display_df['loan_term'].apply(lambda x: f"{x} years")
    display_df['application_date'] = display_df['application_date'].dt.strftime('%Y-%m-%d')
    
    # Rename columns for better display
    display_df.columns = ['Application ID', 'Loan Amount', 'Term', 'Purpose', 'Date', 'Status']
    
    # Display the table
    st.dataframe(display_df, use_container_width=True)
    
    # Application details (expandable)
    st.subheader("Application Details")
    
    # Application selector
    application_ids = sorted_applications['application_id'].tolist()
    selected_application_id = st.selectbox("Select an application to view details:", application_ids)
    
    # Load selected application details
    application_details = load_application_by_id(selected_application_id)
    
    if application_details:
        # Create tabs for different aspects of the application
        tabs = st.tabs(["Overview", "Timeline", "Documents"])
        
        # Overview tab
        with tabs[0]:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Loan Information")
                st.write(f"**Amount:** {format_currency(application_details.get('loan_amount', 0))}")
                st.write(f"**Term:** {application_details.get('loan_term', 0)} years")
                st.write(f"**Purpose:** {application_details.get('purpose', '')}")
                
                # Calculate monthly payment (using a fixed interest rate for illustration)
                interest_rate = 5.99  # Example fixed rate
                monthly_payment = calculate_monthly_payment(
                    application_details.get('loan_amount', 0),
                    application_details.get('loan_term', 0),
                    interest_rate
                )
                st.write(f"**Estimated Monthly Payment:** {format_currency(monthly_payment)} (at {interest_rate}% interest rate)")
                
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
                
                if application_details.get('officer_notes', ''):
                    st.write("**Notes from Loan Officer:**")
                    st.write(application_details.get('officer_notes', ''))
            
            with col2:
                st.subheader("Applicant Information")
                st.write(f"**Name:** {application_details.get('applicant_name', '')}")
                st.write(f"**Email:** {application_details.get('email', '')}")
                st.write(f"**Phone:** {application_details.get('phone', '')}")
                
                st.subheader("Financial Information")
                st.write(f"**Annual Income:** {format_currency(application_details.get('annual_income', 0))}")
                st.write(f"**Employment Status:** {application_details.get('employment_status', '')}")
                st.write(f"**Credit Score:** {application_details.get('credit_score', 0)}")
                st.write(f"**Monthly Debt:** {format_currency(application_details.get('monthly_debt', 0))}")
                
                # Calculate and display DTI ratio
                annual_income = application_details.get('annual_income', 0)
                monthly_debt = application_details.get('monthly_debt', 0)
                if annual_income > 0:
                    monthly_income = annual_income / 12
                    dti_ratio = (monthly_debt / monthly_income) * 100
                    st.write(f"**Debt-to-Income Ratio:** {dti_ratio:.1f}%")
                
                # Display model score if available
                if 'model_score' in application_details and application_details['model_score'] > 0:
                    st.subheader("Application Score")
                    model_score = application_details['model_score']
                    if model_score >= 80:
                        st.success(f"Score: {model_score}/100")
                    elif model_score >= 60:
                        st.info(f"Score: {model_score}/100")
                    else:
                        st.warning(f"Score: {model_score}/100")
        
        # Timeline tab
        with tabs[1]:
            st.subheader("Application Timeline")
            
            # Generate timeline events
            events = generate_application_timeline(application_details)
            
            if events:
                for i, event in enumerate(events):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.write(f"**{event['date'].strftime('%Y-%m-%d %H:%M')}**")
                    with col2:
                        st.write(f"**{event['event']}**")
                        st.write(event['description'])
                    
                    if i < len(events) - 1:
                        st.divider()
            else:
                st.info("No timeline events available.")
        
        # Documents tab
        with tabs[2]:
            st.subheader("Application Documents")
            st.info("No documents available for this application.")
