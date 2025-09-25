from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from ..database import get_db
from ..models import Product
from shared.schemas import ProductCreate, ProductResponse, ProductUpdate

from dependencies import get_product_or_404
from ..event_handlers import publish_product_updated


router = APIRouter(prefix="/products", tags=["products"])


# 🔄 REST API ENDPOINTS
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """REST API: Create product"""
    product_id = str(uuid.uuid4())

    db_product = Product(
        id=product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        category=product.category,
        stock=product.stock,
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product  # FastAPI automatically converts to ProductResponse


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """REST API: Get products"""
    query = db.query(Product)

    if category:
        query = query.filter(Product.category == category)

    products = query.offset(skip).limit(limit).all()
    return products  # FastAPI automatically converts to ProductResponse


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product: Product = Depends(get_product_or_404)):
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_update: ProductUpdate,
    product: Product = Depends(get_product_or_404),
    db: Session = Depends(get_db),
):
    update_data = product_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)

    # 🎯 MESSAGE QUEUE: Publish product update event
    await publish_product_updated(product.__dict__)

    return product  # FastAPI automatically converts to ProductResponse


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product: Product = Depends(get_product_or_404), db: Session = Depends(get_db)
):
    db.delete(product)
    db.commit()


@router.get("/{product_id}/stock", response_model=dict)
async def get_product_stock(product: Product = Depends(get_product_or_404)):
    return {"product_id": product.id, "stock": product.stock}


# @router.patch("/{product_id}/stock", response_model=ProductResponse)
@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_stock(
    product_id: str,
    stock_data: dict,
    product: Product = Depends(get_product_or_404),
    db: Session = Depends(get_db),
):
    new_stock = stock_data.get("stock")
    if new_stock is not None:
        product.stock = stock_data.get("stock", product.stock)
        product.updated_at = datetime.now()
        db.commit()
        db.refresh(product)

        # 🎯 MESSAGE QUEUE: Publish inventory update
        await publish_product_updated({"product_id": product_id, "stock": new_stock})
    return product  # FastAPI automatically converts to ProductResponse
