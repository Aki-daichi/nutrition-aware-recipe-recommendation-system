"""
Backend package utilities and helper functions
"""

def format_response(data, message="Success", status_code=200):
    """
    Format API response consistently
    
    Args:
        data: Response data
        message: Status message
        status_code: HTTP status code
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success" if 200 <= status_code < 300 else "error",
        "message": message,
        "data": data,
        "status_code": status_code
    }


def validate_email(email):
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def calculate_bmi(weight_kg, height_m):
    """Calculate Body Mass Index"""
    return weight_kg / (height_m ** 2)


def calculate_daily_calories_needed(weight_kg, height_cm, age, gender, activity_level=1.5):
    """
    Calculate daily calorie needs using Mifflin-St Jeor equation
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years
        gender: 'male' or 'female'
        activity_level: 1.2 (sedentary) to 1.9 (very active)
    """
    if gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    return bmr * activity_level
