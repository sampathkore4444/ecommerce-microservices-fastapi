import uvicorn
from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

app = FastAPI(title="Product Service", version="1.0.0")

# In-memory database
products_db = {}


# Models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock: int


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    stock: int
    created_at: datetime


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[str] = None


@app.post("/products/", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    product_id = str(uuid.uuid4())

    product_data = {
        "id": product_id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "stock": product.stock,
        "created_at": datetime.now(),
    }

    # Save to database
    products_db[product_id] = product_data

    return product_data


@app.get("/products/", response_model=List[ProductResponse])
async def get_all_products(product_category: Optional[str] = None):
    if product_category is None:
        return list(products_db.values())
    else:
        custom_prods = []
        print("All products=", products_db.values())
        print("product_category=", product_category)
        for product in products_db.values():
            print("product category=", product["category"])
            if product["category"] == product_category:
                custom_prods.append(product)
        return custom_prods


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    else:
        return products_db[product_id]


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, prod_update: ProductUpdate):
    if product_id not in products_db:
        return HTTPException(status_code=404, detail="Product not found")
    else:
        # get the product data for that product id
        product_data = products_db[product_id]

        # update the above product data with the new data receieved in the api
        if prod_update.name is not None:
            product_data["name"] = prod_update.name
        if prod_update.description is not None:
            product_data["description"] = prod_update.description
        if prod_update.price is not None:
            product_data["price"] = prod_update.price
        if prod_update.category is not None:
            product_data["category"] = prod_update.category
        if prod_update.stock is not None:
            product_data["stock"] = prod_update.stock

        # Save back to database
        products_db[product_id] = product_data

        return products_db


@app.delete("/products/", status_code=204)
async def delete_product(product_id: str):
    if product_id in products_db:
        del products_db[product_id]
    else:
        raise HTTPException(status_code=404, detail="Product not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
