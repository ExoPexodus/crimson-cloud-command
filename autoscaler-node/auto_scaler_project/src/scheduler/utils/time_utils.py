
from datetime import datetime, time
import logging

def is_time_in_range(start_time_str: str, end_time_str: str, current_time: datetime = None) -> bool:
    """
    Check if the current time is within the specified time range.
    
    Args:
        start_time_str: Start time in "HH:MM" format
        end_time_str: End time in "HH:MM" format
        current_time: Current time (optional, defaults to now)
    
    Returns:
        bool: True if current time is within range
    """
    if current_time is None:
        current_time = datetime.now()
    
    try:
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        current_time_only = current_time.time()
        
        # Handle overnight ranges (e.g., 22:00 to 06:00)
        if start_time <= end_time:
            return start_time <= current_time_only <= end_time
        else:
            return current_time_only >= start_time or current_time_only <= end_time
            
    except ValueError as e:
        logging.error(f"Invalid time format: {e}")
        return False

def get_current_time_str() -> str:
    """Get current time as HH:MM string"""
    return datetime.now().strftime('%H:%M')

def parse_cron_expression(cron_expr: str) -> dict:
    """
    Parse a simple cron expression for scheduled scaling.
    Supports basic format: "minute hour * * *"
    
    Args:
        cron_expr: Cron expression string
        
    Returns:
        dict: Parsed cron components
    """
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression format")
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'day_of_week': parts[4]
    }
