import time
import logging
import json
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from logger_config import log_api_request, log_authentication_event


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger('api_middleware')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Log request start
        self.logger.info(f"🌐 {request.method} {request.url.path} - START", extra={
            'method': request.method,
            'endpoint': request.url.path,
            'ip_address': client_ip,
            'user_agent': request.headers.get('user-agent', 'Unknown'),
            'query_params': str(request.query_params) if request.query_params else None,
        })
        
        # Log request headers (excluding sensitive ones)
        headers_to_log = {}
        sensitive_headers = {'authorization', 'x-api-key', 'cookie'}
        for name, value in request.headers.items():
            if name.lower() not in sensitive_headers:
                headers_to_log[name] = value
            else:
                headers_to_log[name] = '[REDACTED]'
        
        self.logger.debug(f"📋 Request headers: {json.dumps(headers_to_log)}")
        
        # Try to log request body for non-GET requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await self.get_request_body(request)
                if body:
                    # Redact sensitive fields
                    safe_body = self.redact_sensitive_data(body)
                    self.logger.debug(f"📤 Request body: {json.dumps(safe_body) if isinstance(safe_body, dict) else safe_body}")
            except Exception as e:
                self.logger.debug(f"⚠️ Could not log request body: {e}")
        
        # Process request
        response = None
        error = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            error = str(e)
            self.logger.error(f"❌ Request failed with exception: {error}")
            # Create error response
            from fastapi.responses import JSONResponse
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
            status_code = 500
        
        # Calculate response time
        end_time = time.time()
        response_time = end_time - start_time
        
        # Extract user info if available
        user_id = None
        if hasattr(request.state, 'user'):
            user_id = getattr(request.state.user, 'id', None)
        
        # Log response
        log_level = self.get_log_level(status_code)
        self.logger.log(log_level, f"📨 {request.method} {request.url.path} - {status_code} ({response_time:.3f}s)", extra={
            'method': request.method,
            'endpoint': request.url.path,
            'status_code': status_code,
            'response_time': response_time,
            'ip_address': client_ip,
            'user_id': user_id,
        })
        
        # Log to structured API log
        log_api_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            response_time=response_time,
            user_id=str(user_id) if user_id else None,
            ip_address=client_ip,
            error=error
        )
        
        # Log authentication events
        if request.url.path.startswith('/auth/'):
            event_type = self.get_auth_event_type(request.url.path, request.method)
            if event_type:
                success = 200 <= status_code < 300
                log_authentication_event(
                    event_type=event_type,
                    success=success,
                    ip_address=client_ip,
                    details=f"Status: {status_code}"
                )
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return 'unknown'
    
    async def get_request_body(self, request: Request) -> Optional[dict]:
        """Safely extract request body"""
        try:
            # Get content type
            content_type = request.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                body = await request.body()
                if body:
                    return json.loads(body.decode('utf-8'))
            elif 'application/x-www-form-urlencoded' in content_type:
                form_data = await request.form()
                return dict(form_data)
        except Exception:
            pass
        
        return None
    
    def redact_sensitive_data(self, data) -> dict:
        """Remove sensitive information from request data"""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'api_key',
            'access_token', 'refresh_token', 'authorization'
        }
        
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = self.redact_sensitive_data(value)
            else:
                redacted[key] = value
        
        return redacted
    
    def get_log_level(self, status_code: int) -> int:
        """Determine log level based on status code"""
        if status_code >= 500:
            return logging.ERROR
        elif status_code >= 400:
            return logging.WARNING
        else:
            return logging.INFO
    
    def get_auth_event_type(self, path: str, method: str) -> Optional[str]:
        """Determine authentication event type from path"""
        if path == '/auth/login' and method == 'POST':
            return 'LOGIN'
        elif path == '/auth/register' and method == 'POST':
            return 'REGISTER'
        elif path == '/auth/keycloak/login' and method == 'POST':
            return 'KEYCLOAK_LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        
        return None