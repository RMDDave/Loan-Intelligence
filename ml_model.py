import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import pickle
import os
from datetime import datetime

# File to store the trained model
MODEL_FILE = "loan_approval_model.pkl"

def train_model_if_needed():
    """Train the loan approval model if it doesn't exist"""
    if os.path.exists(MODEL_FILE):
        # If model already exists, no need to retrain
        return
    
    # Check if we have enough applications for training
    if os.path.exists("loan_applications.csv"):
        applications_df = pd.read_csv("loan_applications.csv")
        # Only train if we have at least 10 applications with decisions
        decided_apps = applications_df[applications_df['status'].isin(['approved', 'rejected'])]
        if len(decided_apps) >= 10:
            # Enough data to train a simple model
            X = decided_apps[[
                'loan_amount', 'loan_term', 'annual_income', 'employment_length',
                'credit_score', 'monthly_debt'
            ]]
            y = (decided_apps['status'] == 'approved').astype(int)
            
            # Train a simple RandomForest model
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X, y)
            
            # Save the model
            with open(MODEL_FILE, 'wb') as f:
                pickle.dump(model, f)
            return
    
    # Not enough real data, create a basic rule-based model
    model = _create_rule_based_model()
    
    # Save the model
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)

def _create_rule_based_model():
    """Create a simple rule-based model"""
    # This is a dummy class that implements a predict_proba method
    class RuleBasedModel:
        def predict_proba(self, X):
            # X should have: loan_amount, loan_term, annual_income, employment_length, credit_score, monthly_debt
            results = []
            for i in range(len(X)):
                # Extract features
                loan_amount = X.iloc[i]['loan_amount'] if isinstance(X, pd.DataFrame) else X[i][0]
                annual_income = X.iloc[i]['annual_income'] if isinstance(X, pd.DataFrame) else X[i][2]
                credit_score = X.iloc[i]['credit_score'] if isinstance(X, pd.DataFrame) else X[i][4]
                monthly_debt = X.iloc[i]['monthly_debt'] if isinstance(X, pd.DataFrame) else X[i][5]
                
                # Calculate debt-to-income ratio
                monthly_income = annual_income / 12
                dti_ratio = monthly_debt / monthly_income if monthly_income > 0 else 1
                
                # Calculate loan amount to income ratio
                loan_to_income = loan_amount / annual_income if annual_income > 0 else 1
                
                # Simple scoring logic
                base_score = 0.5
                
                # Credit score factor (higher is better)
                credit_factor = (credit_score - 300) / 500  # Normalize from 300-800 range to 0-1
                credit_factor = max(0, min(1, credit_factor))  # Clamp to 0-1
                
                # DTI factor (lower is better)
                dti_factor = max(0, min(1, 1 - dti_ratio))  # Lower DTI is better
                
                # Loan to income factor (lower is better)
                lti_factor = max(0, min(1, 1 - loan_to_income))  # Lower ratio is better
                
                # Combine factors
                score = base_score + 0.2 * credit_factor + 0.15 * dti_factor + 0.15 * lti_factor
                score = max(0.05, min(0.95, score))  # Clamp to avoid extremes
                
                results.append([1 - score, score])  # [probability of 0, probability of 1]
            
            return np.array(results)
    
    return RuleBasedModel()

def predict_approval(application_data):
    """Predict the approval probability for a loan application"""
    # Make sure we have a model
    train_model_if_needed()
    
    # Load the model
    with open(MODEL_FILE, 'rb') as f:
        model = pickle.load(f)
    
    # Extract relevant features
    features = pd.DataFrame({
        'loan_amount': [float(application_data.get('loan_amount', 0))],
        'loan_term': [int(application_data.get('loan_term', 0))],
        'annual_income': [float(application_data.get('annual_income', 0))],
        'employment_length': [int(application_data.get('employment_length', 0))],
        'credit_score': [int(application_data.get('credit_score', 0))],
        'monthly_debt': [float(application_data.get('monthly_debt', 0))]
    })
    
    # Get prediction probability
    prob = model.predict_proba(features)[0][1]  # Probability of class 1 (approved)
    
    # Convert to a score from 0-100
    score = int(prob * 100)
    
    return score

def get_model_explanation(application_data):
    """Get an explanation of the model's decision"""
    # Extract relevant features
    loan_amount = float(application_data.get('loan_amount', 0))
    loan_term = int(application_data.get('loan_term', 0))
    annual_income = float(application_data.get('annual_income', 0))
    credit_score = int(application_data.get('credit_score', 0))
    monthly_debt = float(application_data.get('monthly_debt', 0))
    
    # Calculate derived metrics
    monthly_income = annual_income / 12
    dti_ratio = monthly_debt / monthly_income if monthly_income > 0 else float('inf')
    monthly_payment = loan_amount / loan_term if loan_term > 0 else float('inf')
    payment_to_income = monthly_payment / monthly_income if monthly_income > 0 else float('inf')
    
    # Generate explanations
    explanations = []
    
    # Credit score explanation
    if credit_score >= 750:
        explanations.append("Your excellent credit score is favorable for approval.")
    elif credit_score >= 700:
        explanations.append("Your good credit score is a positive factor.")
    elif credit_score >= 650:
        explanations.append("Your fair credit score may impact your approval odds.")
    elif credit_score >= 600:
        explanations.append("Your below-average credit score is a concern.")
    else:
        explanations.append("Your credit score is too low for most standard loans.")
    
    # DTI explanation
    if dti_ratio <= 0.2:
        explanations.append("Your very low debt-to-income ratio strongly favors approval.")
    elif dti_ratio <= 0.36:
        explanations.append("Your debt-to-income ratio is within acceptable limits.")
    elif dti_ratio <= 0.43:
        explanations.append("Your debt-to-income ratio is slightly elevated.")
    else:
        explanations.append("Your high debt-to-income ratio may limit approval chances.")
    
    # Payment to income explanation
    if payment_to_income <= 0.1:
        explanations.append("The proposed loan payment is easily affordable relative to your income.")
    elif payment_to_income <= 0.28:
        explanations.append("The proposed loan payment is reasonably affordable relative to your income.")
    else:
        explanations.append("The proposed loan payment is high relative to your income.")
    
    # Loan amount to income explanation
    if loan_amount <= annual_income * 0.5:
        explanations.append("Your requested loan amount is conservative relative to your annual income.")
    elif loan_amount <= annual_income * 2:
        explanations.append("Your requested loan amount is reasonable relative to your annual income.")
    else:
        explanations.append("Your requested loan amount is high relative to your annual income.")
    
    return explanations
