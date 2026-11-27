from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List


class RegisterRequest(BaseModel):
    role: str = "retail"
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    unp: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=200)
    legal_address: Optional[str] = Field(None, max_length=300)
    personal_data_consent: bool = Field(...)

    @field_validator("password")
    @classmethod
    def validate_password_by_role(cls, v, info):
        role = info.data.get("role", "retail")
        if role == "wholesale":
            if len(v) < 8:
                raise ValueError("Пароль должен содержать минимум 8 символов")
        else:
            if len(v) < 8:
                raise ValueError("Пароль должен содержать минимум 8 символов")
        return v

    @field_validator("personal_data_consent")
    @classmethod
    def validate_register_consent(cls, v):
        if v is not True:
            raise ValueError("Необходимо дать согласие на обработку персональных данных")
        return v

    @field_validator("unp")
    @classmethod
    def validate_unp(cls, v, info):
        if info.data.get("role") == "wholesale":
            if not v or not v.isdigit() or len(v) != 9:
                raise ValueError("УНП для Беларуси должен состоять ровно из 9 цифр")
        return v



class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class OrderItemSchema(BaseModel):
    product_id: int = Field(..., gt=0)
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=250)
    quantity: int = Field(..., ge=1, le=10000)  # Строго >= 1 шт.!
    unit_price: float = Field(..., ge=0)


class RecipientSchema(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=5, max_length=30)


class DeliverySchema(BaseModel):
    method: str = Field(..., pattern="^(europost|pickup|manager)$")
    city: Optional[str] = Field(None, max_length=100)
    office: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=300)


class LegalEntitySchema(BaseModel):
    company_name: Optional[str] = Field(None, max_length=200)
    unp: Optional[str] = Field(None, max_length=20)


class OrderCreateRequest(BaseModel):
    user_id: Optional[int] = None
    role: str = "retail"
    recipient: RecipientSchema
    delivery: DeliverySchema
    legal_entity: Optional[LegalEntitySchema] = None
    comment: Optional[str] = Field(None, max_length=500)
    products_total_byn: float = Field(..., ge=0)
    items: List[OrderItemSchema] = Field(..., min_length=1, max_length=100)
    personal_data_consent: bool = Field(...)

    @field_validator("personal_data_consent")
    @classmethod
    def validate_order_consent(cls, v):
        if v is not True:
            raise ValueError("Необходимо подтвердить согласие на обработку персональных данных")
        return v



class SwitchRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(retail|wholesale)$")
    unp: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=200)

    @field_validator("unp")
    @classmethod
    def validate_switch_unp(cls, v, info):
        if info.data.get("role") == "wholesale":
            if not v or not v.isdigit() or len(v) != 9:
                raise ValueError("УНП для Беларуси должен состоять ровно из 9 цифр")
        return v

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("code")
    @classmethod
    def validate_reset_code(cls, v):
        clean = v.strip()
        if not clean.isdigit() or len(clean) != 6:
            raise ValueError("Код должен состоять из 6 цифр")
        return clean
