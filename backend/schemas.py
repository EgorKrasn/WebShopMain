from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List


class RegisterRequest(BaseModel):
    role: str = "retail"
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    unp: Optional[str] = None
    company_name: Optional[str] = None
    legal_address: Optional[str] = None

    @field_validator("unp")
    @classmethod
    def validate_unp(cls, v, info):
        if info.data.get("role") == "wholesale":
            if not v or not v.isdigit() or len(v) != 9:
                raise ValueError("УНП для Беларуси должен состоять ровно из 9 цифр")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OrderItemSchema(BaseModel):
    product_id: int
    sku: str
    name: str
    quantity: int
    unit_price: float


class RecipientSchema(BaseModel):
    full_name: str
    phone: str


class DeliverySchema(BaseModel):
    method: str
    city: Optional[str] = None
    office: Optional[str] = None
    address: Optional[str] = None


class LegalEntitySchema(BaseModel):
    company_name: Optional[str] = None
    unp: Optional[str] = None


class OrderCreateRequest(BaseModel):
    user_id: Optional[int] = None
    role: str = "retail"
    recipient: RecipientSchema
    delivery: DeliverySchema
    legal_entity: Optional[LegalEntitySchema] = None
    comment: Optional[str] = None
    products_total_byn: float
    items: List[OrderItemSchema]

class SwitchRoleRequest(BaseModel):
    role: str  # 'retail' или 'wholesale'
    unp: Optional[str] = None
    company_name: Optional[str] = None

    @field_validator("unp")
    @classmethod
    def validate_switch_unp(cls, v, info):
        if info.data.get("role") == "wholesale":
            if not v or not v.isdigit() or len(v) != 9:
                raise ValueError("УНП для Беларуси должен состоять ровно из 9 цифр")
        return v
