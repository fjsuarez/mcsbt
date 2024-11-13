# password_manager.py

import re
import pandas as pd

passwords = {}

def create_new_password():
    username = input("Enter username: ")
    password = input("Enter password: ")
    rating = rate_password(password)
    print(f"Password rating: {rating}/4")
    save_password(username, password)

def rate_password(password):
    return (check_length(password) 
	+ check_symbols(password)
	+ check_numbers(password) 
	+ check_lowercase_and_uppercase(password))

def check_length(password, threshold=10):
    return len(password) >= threshold

def check_symbols(password):
    return bool(re.search(r'[^\w\s]', password))

def check_numbers(password):
    return bool(re.search(r'\d', password))

def check_lowercase_and_uppercase(password):
    return bool(re.search(r'[a-z]', password)) and bool(re.search(r'[A-Z]', password))

def save_password(username, password):
    passwords[username] = password
    print(f"Password for user '{username}' has been saved.")

def export_passwords():
    df = pd.DataFrame(list(passwords.items()), columns=['Username', 'Password'])
    df.to_csv('passwords.csv', index=False)
    print("Passwords have been exported to 'passwords.csv'.")
