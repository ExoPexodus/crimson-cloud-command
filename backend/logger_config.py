import logging
import logging.handlers
import os
import sys
from datetime import datetime
import json
from typing import Any, Dict


class APILoggingFormatter(logging.Formatter):
    """Custom formatter for API logging with structured output"""
    
    def format(self, record):
        # Get basic log info
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_data['response_time'] = record.response_time
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    def format(self, record):
        # Color codes for different log levels
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green  
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        reset_color = '\033[0m'
        
        level_color = colors.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build formatted message
        formatted = f"{level_color}[{timestamp}] {record.levelname:8s} {record.name:20s}{reset_color} | {record.getMessage()}"
        
        # Add extra context if available
        if hasattr(record, 'endpoint'):
            formatted += f" | {record.method} {record.endpoint}"
        if hasattr(record, 'status_code'):
            formatted += f" | Status: {record.status_code}"
        if hasattr(record, 'response_time'):
            formatted += f" | Time: {record.response_time:.3f}s"
            
        return formatted


def setup_logging():
    """Configure comprehensive logging for console output only"""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler with human-readable format - set to DEBUG to see everything
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ConsoleFormatter())
    
    # Add only console handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_specific_loggers_console()
    
    # Log startup message
    logging.info("🚀 Logging system initialized for console output")
    logging.info("📊 All logs will be printed to console/stdout")


def configure_specific_loggers_console():
    """Configure specific loggers for console output only"""
    
    # API request logger
    api_logger = logging.getLogger('api_requests')
    api_logger.setLevel(logging.INFO)
    
    # API middleware logger
    middleware_logger = logging.getLogger('api_middleware')
    middleware_logger.setLevel(logging.DEBUG)
    
    # Authentication logger
    auth_logger = logging.getLogger('authentication')
    auth_logger.setLevel(logging.INFO)
    
    # Main app logger
    main_logger = logging.getLogger('main')
    main_logger.setLevel(logging.DEBUG)
    
    # Services logger
    services_logger = logging.getLogger('services')
    services_logger.setLevel(logging.DEBUG)
    
    # Database logger
    db_logger = logging.getLogger('sqlalchemy.engine')
    db_logger.setLevel(logging.WARNING)  # Only log warnings and errors for DB
    
    # Uvicorn loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def log_api_request(method: str, path: str, status_code: int, response_time: float, 
                   user_id: str = None, ip_address: str = None, request_body: Dict[str, Any] = None,
                   response_body: Dict[str, Any] = None, error: str = None):
    """Log API request with structured data"""
    
    api_logger = logging.getLogger('api_requests')
    
    extra = {
        'method': method,
        'endpoint': path,
        'status_code': status_code,
        'response_time': response_time,
    }
    
    if user_id:
        extra['user_id'] = user_id
    if ip_address:
        extra['ip_address'] = ip_address
        
    message = f"{method} {path} - {status_code} ({response_time:.3f}s)"
    
    if error:
        message += f" - ERROR: {error}"
        api_logger.error(message, extra=extra)
    elif status_code >= 400:
        api_logger.warning(message, extra=extra)
    else:
        api_logger.info(message, extra=extra)


def log_authentication_event(event_type: str, user_email: str = None, success: bool = True, 
                            details: str = None, ip_address: str = None):
    """Log authentication events"""
    
    auth_logger = logging.getLogger('authentication')
    
    extra = {
        'event_type': event_type,
        'success': success,
    }
    
    if user_email:
        extra['user_email'] = user_email
    if ip_address:
        extra['ip_address'] = ip_address
        
    message = f"Auth Event: {event_type}"
    if user_email:
        message += f" for {user_email}"
    message += f" - {'SUCCESS' if success else 'FAILED'}"
    if details:
        message += f" - {details}"
        
    if success:
        auth_logger.info(message, extra=extra)
    else:
        auth_logger.warning(message, extra=extra)


def log_database_operation(operation: str, table: str, record_id: str = None, 
                          success: bool = True, error: str = None):
    """Log database operations"""
    
    db_logger = logging.getLogger('database_operations')
    
    extra = {
        'operation': operation,
        'table': table,
        'success': success,
    }
    
    if record_id:
        extra['record_id'] = record_id
        
    message = f"DB {operation} on {table}"
    if record_id:
        message += f" (ID: {record_id})"
    message += f" - {'SUCCESS' if success else 'FAILED'}"
    if error:
        message += f" - {error}"
        
    if success:
        db_logger.info(message, extra=extra)
    else:
        db_logger.error(message, extra=extra)