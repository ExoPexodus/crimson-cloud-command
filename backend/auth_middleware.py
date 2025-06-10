
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
import secrets
from database import get_db
from models import Node

class APIKeyAuth:
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key for node authentication."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key

async def get_node_from_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Node:
    """Authenticate a node using API key."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    hashed_key = APIKeyAuth.hash_api_key(x_api_key)
    node = db.query(Node).filter(Node.api_key_hash == hashed_key).first()
    
    if not node:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return node
