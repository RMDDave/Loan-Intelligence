import pandas as pd
import os
import hashlib
from datetime import datetime

# File to store user credentials
USER_DATA_FILE = "user_credentials.csv"

def create_user_dataframe():
    """Initialize user dataframe if it doesn't exist"""
    if not os.path.exists(USER_DATA_FILE):
        df = pd.DataFrame(columns=['username', 'password_hash', 'user_type', 'created_at'])
        df.to_csv(USER_DATA_FILE, index=False)
        return df
    return pd.read_csv(USER_DATA_FILE)

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password, user_type):
    """Authenticate a user"""
    # Create user dataframe if it doesn't exist
    create_user_dataframe()
    
    if not os.path.exists(USER_DATA_FILE):
        return False
    
    users_df = pd.read_csv(USER_DATA_FILE)
    
    if users_df.empty:
        return False
    
    # Find the user
    user = users_df[(users_df['username'] == username) & 
                    (users_df['user_type'] == user_type)]
    
    if user.empty:
        return False
    
    # Check password
    password_hash = hash_password(password)
    if user.iloc[0]['password_hash'] == password_hash:
        return True
    
    return False

def create_user(username, password, user_type):
    """Create a new user"""
    # Create user dataframe if it doesn't exist
    users_df = create_user_dataframe()
    
    # Check if username already exists
    if not users_df.empty and username in users_df['username'].values:
        return False
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Create new user
    new_user = pd.DataFrame({
        'username': [username],
        'password_hash': [password_hash],
        'user_type': [user_type],
        'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    })
    
    # Append to existing users
    updated_users = pd.concat([users_df, new_user], ignore_index=True)
    updated_users.to_csv(USER_DATA_FILE, index=False)
    
    return True

def is_loan_officer(username):
    """Check if a user is a loan officer"""
    if not os.path.exists(USER_DATA_FILE):
        return False
    
    users_df = pd.read_csv(USER_DATA_FILE)
    
    if users_df.empty:
        return False
    
    # Find the user
    user = users_df[users_df['username'] == username]
    
    if user.empty:
        return False
    
    return user.iloc[0]['user_type'] == 'loan officer'
