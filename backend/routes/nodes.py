
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from services import NodeService, AnalyticsService
from schemas import NodeResponse, NodeCreate, NodeUpdate, NodeRegisterResponse, NodeRegister
from auth_middleware import get_current_user, get_node_from_api_key
from models import User, Node

router = APIRouter()

@router.get("/", response_model=list[NodeResponse])
async def get_nodes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all nodes"""
    return NodeService.get_nodes(db)

@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get a specific node"""
    node = NodeService.get_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.get("/{node_id}/analytics")
async def get_node_analytics(node_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get analytics for a specific node"""
    node = NodeService.get_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return AnalyticsService.get_node_analytics(db, node_id)

@router.post("/register", response_model=NodeRegisterResponse)
async def register_node(node: NodeRegister, db: Session = Depends(get_db)):
    """Register a new node and generate API key"""
    return NodeService.register_node(db, node)

@router.post("/", response_model=NodeResponse)
async def create_node(node: NodeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new node"""
    return NodeService.create_node(db, node)

@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, node: NodeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update a node"""
    updated_node = NodeService.update_node(db, node_id, node)
    if not updated_node:
        raise HTTPException(status_code=404, detail="Node not found")
    return updated_node

@router.delete("/{node_id}")
async def delete_node(node_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a node"""
    success = NodeService.delete_node(db, node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}
