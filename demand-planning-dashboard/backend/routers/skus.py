from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import SKU as SKUModel
from schemas import SKU, SKUCreate, SKUUpdate, SKUWithSales

router = APIRouter()

@router.get("/", response_model=List[SKU])
def get_skus(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all SKUs with optional filtering"""
    query = db.query(SKUModel)
    
    if category:
        query = query.filter(SKUModel.category == category)
    if brand:
        query = query.filter(SKUModel.brand == brand)
    
    skus = query.offset(skip).limit(limit).all()
    return skus

@router.get("/{item_id}", response_model=SKUWithSales)
def get_sku(item_id: str, db: Session = Depends(get_db)):
    """Get a specific SKU with sales data and forecasts"""
    sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    return sku

@router.post("/", response_model=SKU)
def create_sku(sku: SKUCreate, db: Session = Depends(get_db)):
    """Create a new SKU"""
    # Check if SKU already exists
    existing_sku = db.query(SKUModel).filter(SKUModel.item_id == sku.item_id).first()
    if existing_sku:
        raise HTTPException(status_code=400, detail="SKU with this item_id already exists")
    
    db_sku = SKUModel(**sku.dict())
    db.add(db_sku)
    db.commit()
    db.refresh(db_sku)
    return db_sku

@router.put("/{item_id}", response_model=SKU)
def update_sku(item_id: str, sku_update: SKUUpdate, db: Session = Depends(get_db)):
    """Update an existing SKU"""
    db_sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    update_data = sku_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sku, field, value)
    
    db.commit()
    db.refresh(db_sku)
    return db_sku

@router.delete("/{item_id}")
def delete_sku(item_id: str, db: Session = Depends(get_db)):
    """Delete a SKU"""
    db_sku = db.query(SKUModel).filter(SKUModel.item_id == item_id).first()
    if not db_sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    db.delete(db_sku)
    db.commit()
    return {"message": "SKU deleted successfully"}
