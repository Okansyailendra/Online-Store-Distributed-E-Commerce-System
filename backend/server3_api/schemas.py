from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    phone_number: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class ProductCreateRequest(BaseModel):
    category_id: str
    sku: str
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    initial_stock: int = Field(default=0, ge=0)
    image_url: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    image_url: Optional[str] = None

class CartItemAddRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, gt=0)

class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)

class OrderStatusUpdateRequest(BaseModel):
    status: str
    tracking_number: Optional[str] = None

class RestockRequest(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
