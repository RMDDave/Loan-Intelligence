import streamlit as st
import pandas as pd
from data import save_application, init_session_state
from ml_model import predict_approval, get_model_explanation
from utils import validate_email, validate_phone, format_currency, calculate_monthly_payment

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="Apply for Loan",
    page_icon="📝",
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
st.title("Loan Application Form")
st.write("Complete the form below to apply for a loan.")

# Multi-step form
steps = ["Personal Information", "Loan Details", "Financial Information", "Review & Submit"]
current_step = st.session_state.get("application_step", 0)

# Progress bar
st.progress((current_step) / (len(steps) - 1))
st.subheader(steps[current_step])

# Initialize temp application if not exists
if "temp_application" not in st.session_state:
    st.session_state.temp_application = {}

# Function to handle next/previous navigation
def next_step():
    st.session_state.application_step += 1

def prev_step():
    st.session_state.application_step -= 1

# STEP 1: Personal Information
if current_step == 0:
    # Get existing data if any
    full_name = st.session_state.temp_application.get("full_name", "")
    email = st.session_state.temp_application.get("email", "")
    phone = st.session_state.temp_application.get("phone", "")
    address = st.session_state.temp_application.get("address", "")
    city = st.session_state.temp_application.get("city", "")
    state = st.session_state.temp_application.get("state", "")
    zip_code = st.session_state.temp_application.get("zip_code", "")
    
    # Form fields
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name*", value=full_name)
        email = st.text_input("Email Address*", value=email)
        phone = st.text_input("Phone Number*", value=phone)
    
    with col2:
        address = st.text_input("Street Address*", value=address)
        city = st.text_input("City*", value=city)
        state = st.selectbox("State*", 
                           ["Select a state", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"],
                           index=0 if not state else ["Select a state", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
                                                    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
                                                    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
                                                    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
                                                    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"].index(state))
        zip_code = st.text_input("ZIP Code*", value=zip_code)
    
    # Validate inputs
    all_fields_filled = all([full_name, email, phone, address, city, state != "Select a state", zip_code])
    email_valid = validate_email(email) if email else False
    phone_valid = validate_phone(phone) if phone else False
    zip_valid = len(zip_code) == 5 and zip_code.isdigit() if zip_code else False
    
    # Show validation messages
    if not email_valid and email:
        st.warning("Please enter a valid email address.")
    if not phone_valid and phone:
        st.warning("Please enter a valid 10-digit phone number.")
    if not zip_valid and zip_code:
        st.warning("Please enter a valid 5-digit ZIP code.")
    
    # Save data to session state
    st.session_state.temp_application.update({
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "address": address,
        "city": city,
        "state": state if state != "Select a state" else "",
        "zip_code": zip_code
    })
    
    # Next button
    if st.button("Next: Loan Details", disabled=not (all_fields_filled and email_valid and phone_valid and zip_valid)):
        next_step()

# STEP 2: Loan Details
elif current_step == 1:
    # Get existing data if any
    loan_amount = st.session_state.temp_application.get("loan_amount", "")
    loan_term = st.session_state.temp_application.get("loan_term", 3)
    purpose = st.session_state.temp_application.get("purpose", "")
    
    # Form fields
    col1, col2 = st.columns(2)
    
    with col1:
        loan_amount = st.number_input("Loan Amount ($)*", min_value=1000.0, max_value=1000000.0, value=float(loan_amount) if loan_amount else 10000.0, step=1000.0)
        purpose = st.selectbox("Loan Purpose*", 
                             ["Select a purpose", "Home Purchase", "Home Improvement", "Debt Consolidation", 
                              "Auto Purchase", "Education", "Medical Expenses", "Business", "Other"],
                             index=0 if not purpose else ["Select a purpose", "Home Purchase", "Home Improvement", "Debt Consolidation", 
                                                       "Auto Purchase", "Education", "Medical Expenses", "Business", "Other"].index(purpose))
    
    with col2:
        loan_term = st.selectbox("Loan Term (Years)*", [1, 2, 3, 5, 7, 10, 15, 20, 30], 
                               index=[1, 2, 3, 5, 7, 10, 15, 20, 30].index(loan_term) if loan_term in [1, 2, 3, 5, 7, 10, 15, 20, 30] else 2)
        
        # For "Other" purpose, allow specification
        if purpose == "Other":
            other_purpose = st.text_input("Please specify:", value=st.session_state.temp_application.get("other_purpose", ""))
            st.session_state.temp_application["other_purpose"] = other_purpose
    
    # Calculate estimated monthly payment (using a fixed interest rate for illustration)
    interest_rate = 5.99  # Example fixed rate
    if loan_amount and loan_term:
        monthly_payment = calculate_monthly_payment(loan_amount, loan_term, interest_rate)
        st.info(f"Estimated Monthly Payment: {format_currency(monthly_payment)} (at {interest_rate}% interest rate)")
    
    # Validate inputs
    all_fields_filled = loan_amount > 0 and loan_term > 0 and purpose != "Select a purpose"
    if purpose == "Other":
        all_fields_filled = all_fields_filled and st.session_state.temp_application.get("other_purpose", "")
    
    # Save data to session state
    st.session_state.temp_application.update({
        "loan_amount": loan_amount,
        "loan_term": loan_term,
        "purpose": purpose
    })
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous: Personal Information"):
            prev_step()
    with col2:
        if st.button("Next: Financial Information", disabled=not all_fields_filled):
            next_step()

# STEP 3: Financial Information
elif current_step == 2:
    # Get existing data if any
    annual_income = st.session_state.temp_application.get("annual_income", "")
    employment_status = st.session_state.temp_application.get("employment_status", "")
    employment_length = st.session_state.temp_application.get("employment_length", "")
    home_ownership = st.session_state.temp_application.get("home_ownership", "")
    credit_score = st.session_state.temp_application.get("credit_score", "")
    monthly_debt = st.session_state.temp_application.get("monthly_debt", "")
    
    # Form fields
    col1, col2 = st.columns(2)
    
    with col1:
        annual_income = st.number_input("Annual Income ($)*", min_value=0.0, max_value=10000000.0, value=float(annual_income) if annual_income else 50000.0, step=1000.0)
        employment_status = st.selectbox("Employment Status*", 
                                       ["Select status", "Full-time", "Part-time", "Self-employed", "Unemployed", "Retired"],
                                       index=0 if not employment_status else ["Select status", "Full-time", "Part-time", "Self-employed", "Unemployed", "Retired"].index(employment_status))
        employment_length = st.number_input("Years at Current Employment*", min_value=0, max_value=50, value=int(employment_length) if employment_length else 1)
    
    with col2:
        home_ownership = st.selectbox("Home Ownership*", 
                                    ["Select type", "Own", "Mortgage", "Rent", "Other"],
                                    index=0 if not home_ownership else ["Select type", "Own", "Mortgage", "Rent", "Other"].index(home_ownership))
        credit_score = st.slider("Estimated Credit Score*", min_value=300, max_value=850, value=int(credit_score) if credit_score else 700, step=10)
        monthly_debt = st.number_input("Current Monthly Debt Payments ($)*", min_value=0.0, max_value=1000000.0, value=float(monthly_debt) if monthly_debt else 1000.0, step=100.0)
    
    # Calculate and display DTI ratio
    if annual_income > 0:
        monthly_income = annual_income / 12
        dti_ratio = (monthly_debt / monthly_income) * 100
        st.info(f"Your Debt-to-Income Ratio: {dti_ratio:.1f}%")
        
        if dti_ratio > 43:
            st.warning("Your debt-to-income ratio is higher than 43%, which may affect loan approval.")
    
    # Validate inputs
    all_fields_filled = (
        annual_income >= 0 and
        employment_status != "Select status" and
        employment_length >= 0 and
        home_ownership != "Select type" and
        credit_score >= 300 and
        monthly_debt >= 0
    )
    
    # Save data to session state
    st.session_state.temp_application.update({
        "annual_income": annual_income,
        "employment_status": employment_status,
        "employment_length": employment_length,
        "home_ownership": home_ownership,
        "credit_score": credit_score,
        "monthly_debt": monthly_debt
    })
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous: Loan Details"):
            prev_step()
    with col2:
        if st.button("Next: Review & Submit", disabled=not all_fields_filled):
            # Calculate model score
            model_score = predict_approval(st.session_state.temp_application)
            st.session_state.temp_application["model_score"] = model_score
            next_step()

# STEP 4: Review & Submit
elif current_step == 3:
    # Display application summary
    st.subheader("Application Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Personal Information**")
        st.write(f"Name: {st.session_state.temp_application.get('full_name', '')}")
        st.write(f"Email: {st.session_state.temp_application.get('email', '')}")
        st.write(f"Phone: {st.session_state.temp_application.get('phone', '')}")
        st.write(f"Address: {st.session_state.temp_application.get('address', '')}, {st.session_state.temp_application.get('city', '')}, {st.session_state.temp_application.get('state', '')} {st.session_state.temp_application.get('zip_code', '')}")
        
        st.write("**Loan Details**")
        st.write(f"Amount: {format_currency(st.session_state.temp_application.get('loan_amount', 0))}")
        st.write(f"Term: {st.session_state.temp_application.get('loan_term', 0)} years")
        purpose = st.session_state.temp_application.get('purpose', '')
        if purpose == "Other":
            st.write(f"Purpose: Other - {st.session_state.temp_application.get('other_purpose', '')}")
        else:
            st.write(f"Purpose: {purpose}")
    
    with col2:
        st.write("**Financial Information**")
        st.write(f"Annual Income: {format_currency(st.session_state.temp_application.get('annual_income', 0))}")
        st.write(f"Employment: {st.session_state.temp_application.get('employment_status', '')} ({st.session_state.temp_application.get('employment_length', 0)} years)")
        st.write(f"Home Ownership: {st.session_state.temp_application.get('home_ownership', '')}")
        st.write(f"Credit Score: {st.session_state.temp_application.get('credit_score', 0)}")
        st.write(f"Monthly Debt: {format_currency(st.session_state.temp_application.get('monthly_debt', 0))}")
        
        # Calculate and display DTI ratio
        annual_income = st.session_state.temp_application.get('annual_income', 0)
        monthly_debt = st.session_state.temp_application.get('monthly_debt', 0)
        if annual_income > 0:
            monthly_income = annual_income / 12
            dti_ratio = (monthly_debt / monthly_income) * 100
            st.write(f"Debt-to-Income Ratio: {dti_ratio:.1f}%")
    
    # Display approval score
    model_score = st.session_state.temp_application.get("model_score", 0)
    
    st.subheader("Preliminary Assessment")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display score gauge
        if model_score >= 80:
            st.success(f"Score: {model_score}/100")
        elif model_score >= 60:
            st.info(f"Score: {model_score}/100")
        else:
            st.warning(f"Score: {model_score}/100")
    
    with col2:
        # Display score explanation
        explanations = get_model_explanation(st.session_state.temp_application)
        for explanation in explanations:
            st.write(f"• {explanation}")
    
    # Terms and conditions
    st.subheader("Terms and Conditions")
    terms_agreed = st.checkbox("I confirm that all information provided is accurate and complete. I authorize the lender to obtain credit reports and verify information as needed for this application.")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous: Financial Information"):
            prev_step()
    with col2:
        if st.button("Submit Application", disabled=not terms_agreed):
            # Save application to database
            application_id = save_application(st.session_state.temp_application)
            
            # Show success message
            st.success(f"Application submitted successfully! Your application ID is: {application_id}")
            
            # Clear form data
            st.session_state.temp_application = {}
            st.session_state.application_step = 0
            
            # Add a button to view applications
            if st.button("View My Applications"):
                st.switch_page("pages/02_My_Applications.py")
