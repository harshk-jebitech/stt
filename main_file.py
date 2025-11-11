# main.py

import os
import requests  # unused import — SonarQube should flag this

# 🚨 Hardcoded secret for test (Sonar should flag this as a security issue)
API_KEY = "sk_test_1234567890abcdef"

def divide(a, b):
    # 🚨 Potential bug: no division by zero check
    return a / b

def greet_user(username):
    # 🚨 Code smell: not using f-string
    print("Hello " + username)

def insecure_function():
    # 🚨 Security Hotspot: executing shell command
    os.system("echo 'Running command without sanitization'")

def main():
    greet_user("Harsh")
    result = divide(10, 0)  # 🚨 This should raise ZeroDivisionError
    print("Result:", result)

if __name__ == "__main__":
    main()