import io
import json
import os
import re
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.background import BackgroundTask


from sqlalchemy.orm import Session
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import models
import schemas
import security
from database import engine, get_db, SessionLocal

from sqlalchemy import text

load_dotenv()

ENV = os.getenv("ENV", "development")
is_prod = ENV == "production"

models.Base.metadata.create_all(bind=engine)

def ensure_product_promo_columns():
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(products)")).fetchall()]
        if "old_retail_price" not in cols:
            conn.execute(text("ALTER TABLE products ADD COLUMN old_retail_price FLOAT"))
        if "old_wholesale_price" not in cols:
            conn.execute(text("ALTER TABLE products ADD COLUMN old_wholesale_price FLOAT"))
        if "promo_label" not in cols:
            conn.execute(text("ALTER TABLE products ADD COLUMN promo_label VARCHAR"))

ensure_product_promo_columns()

# Инициализация лимитера запросов (защита от брутфорса и DDoS на уровне API)
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="API Интернет-магазина ООО «Сандринтайм»",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Настройка CORS строго для разрешённых доменов из .env
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Middleware защитных HTTP-заголовков
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_initial_products():
    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            initial_products = [
                models.Product(
                    id=101, sku="ST-1111", group_id="alarm-round", color_name="Чёрный",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Чёрный)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Компактный настольный будильник с чётким контрастным циферблатом и надёжным кварцевым механизмом.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/1111.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=102, sku="ST-1112", group_id="alarm-round", color_name="Розовый",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Розовый)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Компактный настольный будильник в нежном розовом корпусе с чётким циферблатом.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/1112.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=103, sku="ST-2673", group_id="alarm-round", color_name="Белый",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Белый)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Универсальный белый будильник для спальни, детской комнаты или рабочего стола.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/2673-1.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=104, sku="ST-2401", group_id="alarm-round", color_name="Сиреневый",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Сиреневый)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Стильный настольный будильник в сиреневом корпусе с хорошо читаемыми цифрами.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 24.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=105, sku="ST-2501", group_id="alarm-round", color_name="Салатовый",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Салатовый)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Яркий салатовый будильник с громким сигналом и крупным циферблатом.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 25.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=106, sku="ST-2701", group_id="alarm-round", color_name="Голубой",
                    category="Интерьерные и настенные", name="Будильник кварцевый «Classic Round» (Голубой)",
                    specs="Тихий ход • Подсветка • Батарейка AA",
                    description="Настольный кварцевый будильник в голубом корпусе.",
                    mechanism="Кварцевый", case_material="Ударопрочный пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 27.png", retail_price=24.00, wholesale_price=15.50,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=201, sku="ST-2901", group_id="alarm-rect", color_name="Серый",
                    category="Интерьерные и настенные", name="Будильник настольный «Modern Square» (Серый)",
                    specs="Широкий экран • Кварцевый механизм • AA",
                    description="Устойчивый прямоугольный будильник с крупными арабскими цифрами.",
                    mechanism="Кварцевый", case_material="Пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 29.png", retail_price=26.00, wholesale_price=16.90,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=202, sku="ST-3001", group_id="alarm-rect", color_name="Белый",
                    category="Интерьерные и настенные", name="Будильник настольный «Modern Square» (Белый)",
                    specs="Широкий экран • Кварцевый механизм • AA",
                    description="Лаконичный белый будильник прямоугольной формы для дома и офиса.",
                    mechanism="Кварцевый", case_material="Пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 30.png", retail_price=26.00, wholesale_price=16.90,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=203, sku="ST-3101", group_id="alarm-rect", color_name="Сиреневый",
                    category="Интерьерные и настенные", name="Будильник настольный «Modern Square» (Сиреневый)",
                    specs="Широкий экран • Кварцевый механизм • AA",
                    description="Прямоугольный настольный будильник в сиреневом исполнении.",
                    mechanism="Кварцевый", case_material="Пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 31.png", retail_price=26.00, wholesale_price=16.90,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=204, sku="ST-3201", group_id="alarm-rect", color_name="Голубой",
                    category="Интерьерные и настенные", name="Будильник настольный «Modern Square» (Голубой)",
                    specs="Широкий экран • Кварцевый механизм • AA",
                    description="Прямоугольный настольный будильник в голубом корпусе.",
                    mechanism="Кварцевый", case_material="Пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 32.png", retail_price=26.00, wholesale_price=16.90,
                    min_wholesale_qty=10, stock=45,
                ),
                models.Product(
                    id=205, sku="ST-3301", group_id="alarm-rect", color_name="Салатовый",
                    category="Интерьерные и настенные", name="Будильник настольный «Modern Square» (Салатовый)",
                    specs="Широкий экран • Кварцевый механизм • AA",
                    description="Яркий салатовый будильник с широким циферблатом.",
                    mechanism="Кварцевый", case_material="Пластик", warranty="12 месяцев",
                    icon="⏰", image="/images/Frame 33.png", retail_price=26.00, wholesale_price=16.90,
                    min_wholesale_qty=10, stock=0,
                ),
            ]
            db.add_all(initial_products)
            db.commit()
    finally:
        db.close()


seed_initial_products()


def seed_admin_user():
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@sandrintime.by")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            return
        existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not existing_admin:
            admin = models.User(
                role="admin",
                wholesale_status="approved",
                email=admin_email,
                hashed_password=pwd_context.hash(admin_password),
                full_name="Администратор Сандринтайм",
                phone="+375 (29) 651-19-83",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


seed_admin_user()


#1. Получить весь каталог товаров

@app.get("/api/products")
@limiter.limit("60/minute")
def get_products(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.Product).all()

    groups = {}
    for p in items:
        if p.group_id:
            groups.setdefault(p.group_id, []).append(p)

    result = []
    for p in items:
        variants = []
        if p.group_id and len(groups.get(p.group_id, [])) > 1:
            variants = [
                {
                    "id": v.id,
                    "sku": v.sku,
                    "colorName": v.color_name or v.name,
                    "image": v.image,
                    "icon": v.icon,
                    "stock": v.stock,
                }
                for v in groups[p.group_id]
            ]

        product_attributes = p.attributes
        if not product_attributes:
            product_attributes = []
            if p.specs:
                product_attributes.append({"label": "Кратко", "value": p.specs})
            if p.mechanism:
                product_attributes.append({"label": "Механизм", "value": p.mechanism})
            if p.case_material:
                product_attributes.append({"label": "Материал", "value": p.case_material})
            if p.warranty:
                product_attributes.append({"label": "Гарантия", "value": p.warranty})

        discount_percent = 0
        if p.old_retail_price and p.old_retail_price > p.retail_price and p.retail_price > 0:
            discount_percent = round((1 - p.retail_price / p.old_retail_price) * 100)

        result.append({
            "id": p.id,
            "sku": p.sku,
            "groupId": p.group_id,
            "colorName": p.color_name,
            "category": p.category,
            "subcategory": p.subcategory,
            "name": p.name,
            "specs": p.specs,
            "description": p.description,
            "mechanism": p.mechanism,
            "caseMaterial": p.case_material,
            "warranty": p.warranty,
            "attributes": product_attributes,
            "icon": p.icon,
            "image": p.image,
            "retailPrice": p.retail_price,
            "wholesalePrice": p.wholesale_price,
            "oldRetailPrice": p.old_retail_price,
            "oldWholesalePrice": p.old_wholesale_price,
            "promoLabel": p.promo_label,
            "discountPercent": discount_percent,
            "minWholesaleQty": p.min_wholesale_qty,
            "stock": p.stock,
            "variants": variants,
        })


    return result


def build_auth_response(user: models.User):
    token = security.create_access_token(user_id=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "role": user.role,
            "wholesaleStatus": user.wholesale_status,
            "email": user.email,
            "name": user.company_name if user.role == "wholesale" else user.full_name,
            "companyName": user.company_name,
            "contactName": user.full_name,
            "unp": user.unp,
        }
    }


@app.post("/api/auth/login")
@limiter.limit("5/minute")
def login_user(request: Request, payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    return build_auth_response(user)


@app.post("/api/auth/register")
@limiter.limit("3/hour")
def register_user(request: Request, payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже зарегистрирован")

    is_wholesale_request = payload.role == "wholesale"
    clean_unp = re.sub(r"\D", "", payload.unp or "") if is_wholesale_request else None

    if is_wholesale_request:
        if len(clean_unp) != 9:
            raise HTTPException(status_code=400, detail="УНП должен состоять ровно из 9 цифр")
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=400, detail="Укажите наименование организации или ИП")

    new_user = models.User(
        role="retail",
        wholesale_status="pending" if is_wholesale_request else None,
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        unp=clean_unp,
        company_name=payload.company_name.strip() if (is_wholesale_request and payload.company_name) else None,
        legal_address=payload.legal_address.strip() if (is_wholesale_request and payload.legal_address) else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return build_auth_response(new_user)


@app.patch("/api/auth/role")
@limiter.limit("10/minute")
def switch_user_role(
    request: Request,
    payload: schemas.SwitchRoleRequest,
    current_user: models.User = Depends(security.get_current_user_required),
    db: Session = Depends(get_db)
):
    if payload.role == "wholesale":
        clean_unp = re.sub(r"\D", "", payload.unp or "")
        if len(clean_unp) != 9:
            raise HTTPException(status_code=400, detail="УНП должен состоять ровно из 9 цифр")
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=400, detail="Укажите наименование организации или ИП")

        current_user.unp = clean_unp
        current_user.company_name = payload.company_name.strip()

        if current_user.wholesale_status == "approved":
            current_user.role = "wholesale"
        else:
            current_user.role = "retail"
            current_user.wholesale_status = "pending"
    else:
        current_user.role = "retail"

    db.commit()
    db.refresh(current_user)

    return build_auth_response(current_user)


#4. Создание новой заявки (защита от подмены цен и спама заказами)

@app.post("/api/orders")
@limiter.limit("5/minute")
def create_order(
    request: Request,
    payload: schemas.OrderCreateRequest,
    current_user: models.User | None = Depends(security.get_current_user_optional),
    db: Session = Depends(get_db)
):
    is_approved_wholesale = bool(
        current_user
        and current_user.role == "wholesale"
        and current_user.wholesale_status == "approved"
    )
    effective_role = "wholesale" if is_approved_wholesale else "retail"

    if effective_role == "wholesale":
        effective_delivery_method = "manager"
    else:
        if payload.delivery.method not in ("europost", "pickup"):
            raise HTTPException(status_code=400, detail="Некорректный способ доставки")
        effective_delivery_method = payload.delivery.method

    is_europost = effective_delivery_method == "europost"
    initial_status = "europost_pending" if is_europost else "processing"

    new_order = models.Order(
        number="TEMP",
        user_id=current_user.id if current_user else None,
        role=effective_role,
        status=initial_status,
        recipient_name=payload.recipient.full_name.strip(),
        recipient_phone=payload.recipient.phone.strip(),
        delivery_method=effective_delivery_method,
        delivery_city=payload.delivery.city.strip() if (is_europost and payload.delivery.city) else None,
        delivery_office=payload.delivery.office.strip() if (is_europost and payload.delivery.office) else None,
        company_name=current_user.company_name if is_approved_wholesale else None,
        unp=current_user.unp if is_approved_wholesale else None,
        comment=payload.comment.strip() if payload.comment else None,
        products_total_byn=0.0,
    )
    db.add(new_order)
    db.flush()

    new_order.number = f"СТ-{new_order.id:04d}"
    calculated_total = 0.0

    for item in payload.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Товар «{item.name}» не найден в каталоге")
        if product.stock < item.quantity:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара «{product.name}» на складе (доступно: {product.stock} шт.)"
            )
        if is_approved_wholesale and item.quantity < (product.min_wholesale_qty or 1):
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Минимальная оптовая партия для «{product.name}» — {product.min_wholesale_qty} шт."
            )

        actual_unit_price = product.wholesale_price if is_approved_wholesale else product.retail_price
        calculated_total += actual_unit_price * item.quantity

        product.stock -= item.quantity

        db.add(
            models.OrderItem(
                order_id=new_order.id,
                product_id=product.id,
                sku=product.sku,
                name=product.name,
                quantity=item.quantity,
                unit_price=actual_unit_price,
            )
        )

    new_order.products_total_byn = round(calculated_total, 2)
    db.commit()
    db.refresh(new_order)

    return {
        "id": new_order.id,
        "number": new_order.number,
        "status": new_order.status,
        "createdAt": new_order.created_at.strftime("%d.%m.%Y %H:%M"),
    }


@app.get("/api/orders")
def get_my_orders(
    current_user: models.User = Depends(security.get_current_user_required),
    db: Session = Depends(get_db)
):
    orders = (
        db.query(models.Order)
        .filter(models.Order.user_id == current_user.id)
        .order_by(models.Order.id.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "number": o.number,
            "createdAt": o.created_at.strftime("%d.%m.%Y %H:%M"),
            "status": o.status,
            "trackCode": o.track_code,
            "recipient": {
                "full_name": o.recipient_name,
                "phone": o.recipient_phone,
            },
            "delivery": {
                "method": o.delivery_method,
                "city": o.delivery_city,
                "office": o.delivery_office,
            },
            "products_total_byn": o.products_total_byn,
            "items": [
                {
                    "product_id": i.product_id,
                    "sku": i.sku,
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                }
                for i in o.items
            ],
        }
        for o in orders
    ]


def seed_initial_categories():
    db = SessionLocal()
    try:
        if db.query(models.Category).count() == 0:
            default_categories = [
                models.Category(
                    name="Наручные часы",
                    icon="⌚",
                    sort_order=1,
                    subcategories=[
                        "Мужские механические",
                        "Женские кварцевые",
                        "Спортивные и тактические",
                        "Детские часы",
                        "Премиум-сегмент",
                    ],
                ),
                models.Category(
                    name="Интерьерные и настенные",
                    icon="🕰️",
                    sort_order=2,
                    subcategories=[
                        "Большие настенные",
                        "Бесшумные для спальни",
                        "Настольные с будильником",
                        "Каминные и ретро",
                        "Офисные модели",
                    ],
                ),
                models.Category(
                    name="Умные часы и браслеты",
                    icon="📱",
                    sort_order=3,
                    subcategories=[
                        "Смарт-часы для спорта",
                        "Детские часы с GPS",
                        "Фитнес-браслеты",
                        "Зарядные устройства",
                    ],
                ),
                models.Category(
                    name="Ремешки и комплектующие",
                    icon="🔗",
                    sort_order=4,
                    subcategories=[
                        "Кожаные ремешки",
                        "Металлические браслеты",
                        "Силиконовые ремешки",
                        "Элементы питания (батарейки)",
                        "Инструменты для ремонта",
                    ],
                ),
                models.Category(
                    name="Оптовые подборки и боксы",
                    icon="📦",
                    sort_order=5,
                    subcategories=[
                        "Микс-боксы от 10 штук",
                        "Подарочные футляры оптом",
                        "Витринные стойки и подставки",
                        "Сезонные распродажи",
                    ],
                ),
            ]
            db.add_all(default_categories)
            db.commit()
    finally:
        db.close()


seed_initial_categories()

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = (
        db.query(models.Category)
        .order_by(models.Category.sort_order.asc(), models.Category.id.asc())
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "subcategories": c.subcategories or [],
            "sortOrder": c.sort_order,
        }
        for c in cats
    ]


#==========================================


#АДМИН-ПАНЕЛЬ (только для role == 'admin')


#==========================================

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 МБ


MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 МБ на входной файл до сжатия
MAX_IMAGE_DIMENSION = 1000  # Максимальная ширина/высота итогового PNG


def is_valid_image_bytes(header: bytes) -> bool:
    if header.startswith(b"\xff\xd8\xff"):  # JPEG
        return True
    if header.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
        return True
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):  # GIF
        return True
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":  # WEBP
        return True
    return False


def process_image_to_optimized_png(raw_bytes: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            img = ImageOps.exif_transpose(img)

            # Сохраняем альфа-канал (прозрачность) для PNG/WEBP/GIF или переводим в RGB
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

            out_buffer = io.BytesIO()
            img.save(out_buffer, format="PNG", optimize=True)
            return out_buffer.getvalue()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Файл повреждён или не является корректным изображением")


@app.post("/api/admin/upload-image")
async def admin_upload_product_image(
    request: Request,
    file: UploadFile = File(...),
    admin: models.User = Depends(security.get_current_admin_required)
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        raise HTTPException(status_code=400, detail="Допустимы только изображения (JPG, PNG, WEBP, GIF)")

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Размер исходного изображения не должен превышать 10 МБ")

    if not is_valid_image_bytes(content[:16]):
        raise HTTPException(status_code=400, detail="Файл повреждён или не является настоящим изображением")

    optimized_png_bytes = process_image_to_optimized_png(content)

    filename = f"{uuid.uuid4().hex}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(optimized_png_bytes)

    return {"url": f"/uploads/{filename}"}




@app.get("/api/admin/wholesale-requests")
def admin_get_wholesale_requests(
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    users = (
        db.query(models.User)
        .filter(models.User.wholesale_status.isnot(None), models.User.role != "admin")
        .order_by(models.User.id.desc())
        .all()
    )
    return [
        {
            "id": u.id,
            "email": u.email,
            "fullName": u.full_name,
            "phone": u.phone,
            "unp": u.unp,
            "companyName": u.company_name,
            "legalAddress": u.legal_address,
            "role": u.role,
            "wholesaleStatus": u.wholesale_status,
        }
        for u in users
    ]


@app.patch("/api/admin/users/{user_id}/wholesale-status")
def admin_review_wholesale(
    user_id: int,
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    decision = payload.get("decision")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.role == "admin":
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if decision == "approved":
        user.wholesale_status = "approved"
        user.role = "wholesale"
    elif decision == "rejected":
        user.wholesale_status = "rejected"
        user.role = "retail"
    else:
        raise HTTPException(status_code=400, detail="Неверное решение")

    db.commit()
    return {"ok": True, "userId": user.id, "wholesaleStatus": user.wholesale_status}

def adjust_order_stock(db: Session, order: models.Order, restore: bool):
    """
    restore=True  -> возвращает товары из заказа обратно на склад (+quantity)
    restore=False -> списывает товары из заказа со склада (-quantity)
    """
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            continue
        if restore:
            product.stock = (product.stock or 0) + item.quantity
        else:
            if (product.stock or 0) < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Недостаточно товара «{product.name}» на складе для возобновления заказа (доступно: {product.stock} шт.)"
                )
            product.stock -= item.quantity

@app.get("/api/admin/orders")
def admin_get_all_orders(
    status_filter: str = "active",  # 'active' (в работе) или 'archive' / 'completed' (выполненные и отменённые)
    limit: int = 20,
    offset: int = 0,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    query = db.query(models.Order)

    if status_filter in ("completed", "archive"):
        query = query.filter(models.Order.status.in_(["completed", "cancelled"]))
    elif status_filter == "active":
        query = query.filter(models.Order.status.notin_(["completed", "cancelled"]))

    total_count = query.count()
    orders = (
        query.order_by(models.Order.id.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    items_list = [
        {
            "id": o.id,
            "number": o.number,
            "createdAt": o.created_at.strftime("%d.%m.%Y %H:%M"),
            "role": o.role,
            "status": o.status,
            "trackCode": o.track_code,
            "companyName": o.company_name,
            "unp": o.unp,
            "comment": o.comment,
            "recipient": {
                "full_name": o.recipient_name,
                "phone": o.recipient_phone,
            },
            "delivery": {
                "method": o.delivery_method,
                "city": o.delivery_city,
                "office": o.delivery_office,
            },
            "products_total_byn": o.products_total_byn,
            "items": [
                {
                    "product_id": i.product_id,
                    "sku": i.sku,
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                }
                for i in o.items
            ],
        }
        for o in orders
    ]

    return {
        "items": items_list,
        "total": total_count,
        "hasMore": (offset + len(items_list)) < total_count,
    }


@app.delete("/api/admin/orders/{order_id}")
def admin_delete_order(
    order_id: int,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Если заказ не был отменён ранее и не завершён как проданный — возвращаем остатки на склад
    if order.status not in ("cancelled", "completed"):
        adjust_order_stock(db, order, restore=True)

    db.delete(order)
    db.commit()
    return {"ok": True}



@app.patch("/api/admin/orders/{order_id}")
def admin_update_order(
    order_id: int,
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    old_status = order.status
    new_status = payload.get("status")

    if new_status and new_status != old_status:
        # Переводим в "Отменён" -> возвращаем остатки на склад
        if new_status == "cancelled" and old_status != "cancelled":
            adjust_order_stock(db, order, restore=True)
        # Возвращаем отменённый заказ обратно в работу -> снова списываем со склада
        elif old_status == "cancelled" and new_status != "cancelled":
            adjust_order_stock(db, order, restore=False)

        order.status = new_status

    if "trackCode" in payload:
        order.track_code = (payload["trackCode"] or "").strip() or None

    db.commit()
    return {"ok": True}


@app.post("/api/admin/products")
def admin_create_product(
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    sku = (payload.get("sku") or "").strip()
    if not sku:
        raise HTTPException(status_code=400, detail="Укажите артикул (SKU)")

    existing = db.query(models.Product).filter(models.Product.sku == sku).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Товар с артикулом {sku} уже существует")

    try:
        new_product = models.Product(
            sku=sku,
            group_id=(payload.get("groupId") or "").strip() or None,
            color_name=(payload.get("colorName") or "").strip() or None,
            category=(payload.get("category") or "Наручные часы").strip(),
            subcategory=(payload.get("subcategory") or "").strip() or None,
            name=(payload.get("name") or "").strip(),
            specs=(payload.get("specs") or "").strip(),
            description=(payload.get("description") or "").strip() or None,
            attributes=payload.get("attributes") or None,
            icon=(payload.get("icon") or "⌚").strip(),
            image=(payload.get("image") or "").strip() or None,
            retail_price=max(0.0, float(payload.get("retailPrice") or 0)),
            wholesale_price=max(0.0, float(payload.get("wholesalePrice") or 0)),
            min_wholesale_qty=max(1, int(payload.get("minWholesaleQty") or 5)),
            stock=max(0, int(payload.get("stock") or 0)),
            old_retail_price=float(payload["oldRetailPrice"]) if payload.get("oldRetailPrice") else None,
            old_wholesale_price=float(payload["oldWholesalePrice"]) if payload.get("oldWholesalePrice") else None,
            promo_label=(payload.get("promoLabel") or "").strip() or None,

        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return {"ok": True, "id": new_product.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка сохранения в БД: {str(e)}")



@app.put("/api/admin/products/{product_id}")
def admin_update_product(
    product_id: int,
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if "sku" in payload and payload["sku"]:
        product.sku = payload["sku"].strip()
    if "groupId" in payload:
        product.group_id = (payload["groupId"] or "").strip() or None
    if "colorName" in payload:
        product.color_name = (payload["colorName"] or "").strip() or None
    if "category" in payload and payload["category"]:
        product.category = payload["category"].strip()
    if "subcategory" in payload:
        product.subcategory = (payload["subcategory"] or "").strip() or None
    if "name" in payload and payload["name"]:
        product.name = payload["name"].strip()
    if "specs" in payload:
        product.specs = (payload["specs"] or "").strip()
    if "description" in payload:
        product.description = (payload["description"] or "").strip() or None
    if "attributes" in payload:
        product.attributes = payload["attributes"]
    if "image" in payload:
        product.image = (payload["image"] or "").strip() or None
    if "retailPrice" in payload:
        product.retail_price = max(0.0, float(payload["retailPrice"]))
    if "wholesalePrice" in payload:
        product.wholesale_price = max(0.0, float(payload["wholesalePrice"]))
    if "minWholesaleQty" in payload:
        product.min_wholesale_qty = max(1, int(payload["minWholesaleQty"]))
    if "stock" in payload:
        product.stock = max(0, int(payload["stock"]))
    if "oldRetailPrice" in payload:
        val = payload["oldRetailPrice"]
        product.old_retail_price = float(val) if val not in (None, "", 0, "0") else None
    if "oldWholesalePrice" in payload:
        val = payload["oldWholesalePrice"]
        product.old_wholesale_price = float(val) if val not in (None, "", 0, "0") else None
    if "promoLabel" in payload:
        product.promo_label = (payload["promoLabel"] or "").strip() or None


    db.commit()
    return {"ok": True}


@app.delete("/api/admin/products/{product_id}")
def admin_delete_product(
    product_id: int,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    db.delete(product)
    db.commit()
    return {"ok": True}

def get_real_client_ip(request: Request) -> str:
    return request.headers.get("X-Real-IP") or get_remote_address(request)



# 8. Создать категорию
@app.post("/api/admin/categories")
def admin_create_category(
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Укажите название категории")

    existing = db.query(models.Category).filter(models.Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")

    raw_subs = payload.get("subcategories") or []
    clean_subs = [str(s).strip() for s in raw_subs if str(s).strip()]

    new_cat = models.Category(
        name=name,
        icon=(payload.get("icon") or "⌚").strip(),
        subcategories=clean_subs,
        sort_order=int(payload.get("sortOrder") or 0),
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return {"ok": True, "id": new_cat.id}


# 9. Редактировать категорию (при переименовании автоматически обновляет категорию у товаров!)
@app.put("/api/admin/categories/{category_id}")
def admin_update_category(
    category_id: int,
    payload: dict,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    old_name = cat.name
    new_name = (payload.get("name") or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Название категории не может быть пустым")

    if new_name != old_name:
        duplicate = db.query(models.Category).filter(models.Category.name == new_name).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")
        cat.name = new_name
        # Обновляем название категории у всех привязанных товаров
        db.query(models.Product).filter(models.Product.category == old_name).update(
            {"category": new_name}
        )

    if "icon" in payload and payload["icon"]:
        cat.icon = str(payload["icon"]).strip()

    if "subcategories" in payload and isinstance(payload["subcategories"], list):
        cat.subcategories = [str(s).strip() for s in payload["subcategories"] if str(s).strip()]

    if "sortOrder" in payload:
        cat.sort_order = int(payload["sortOrder"] or 0)

    db.commit()
    return {"ok": True}


# 10. Удалить категорию
@app.delete("/api/admin/categories/{category_id}")
def admin_delete_category(
    category_id: int,
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(cat)
    db.commit()
    return {"ok": True}


# ==========================================
# 11. РЕЗЕРВНОЕ КОПИРОВАНИЕ И МИГРАЦИЯ (.ZIP)
# ==========================================

MAX_BACKUP_SIZE_BYTES = 500 * 1024 * 1024  # 500 МБ


def _cleanup_temp_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


@app.get("/api/admin/backup/export")
def admin_export_backup(
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    categories = (
        db.query(models.Category)
        .order_by(models.Category.sort_order.asc(), models.Category.id.asc())
        .all()
    )
    products = db.query(models.Product).order_by(models.Product.id.asc()).all()

    backup_payload = {
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "icon": c.icon,
                "subcategories": c.subcategories or [],
                "sort_order": c.sort_order or 0,
            }
            for c in categories
        ],
        "products": [
            {
                "id": p.id,
                "sku": p.sku,
                "group_id": p.group_id,
                "color_name": p.color_name,
                "category": p.category,
                "subcategory": p.subcategory,
                "name": p.name,
                "specs": p.specs,
                "description": p.description,
                "mechanism": p.mechanism,
                "case_material": p.case_material,
                "warranty": p.warranty,
                "attributes": p.attributes,
                "icon": p.icon,
                "image": p.image,
                "retail_price": p.retail_price,
                "wholesale_price": p.wholesale_price,
                "old_retail_price": p.old_retail_price,
                "old_wholesale_price": p.old_wholesale_price,
                "promo_label": p.promo_label,
                "min_wholesale_qty": p.min_wholesale_qty,
                "stock": p.stock,
            }
            for p in products
        ],
    }

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp_path = tmp_file.name
    tmp_file.close()

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "backup_data.json",
                json.dumps(backup_payload, ensure_ascii=False, indent=2)
            )

            if os.path.exists(UPLOAD_DIR):
                for root, _, files in os.walk(UPLOAD_DIR):
                    for file_name in files:
                        full_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(full_path, UPLOAD_DIR).replace("\\", "/")
                        zf.write(full_path, arcname=f"uploads/{rel_path}")
    except Exception:
        _cleanup_temp_file(tmp_path)
        raise

    date_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"sandrintime-backup-{date_stamp}.zip"

    return FileResponse(
        path=tmp_path,
        media_type="application/zip",
        filename=filename,
        headers={
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
        background=BackgroundTask(_cleanup_temp_file, tmp_path),
    )


@app.post("/api/admin/backup/import")
async def admin_import_backup(
    file: UploadFile = File(...),
    admin: models.User = Depends(security.get_current_admin_required),
    db: Session = Depends(get_db)
):
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Загрузите файл резервной копии в формате .zip")

    content = await file.read()
    if len(content) > MAX_BACKUP_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Размер архива не должен превышать 150 МБ")

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Файл повреждён или не является корректным ZIP-архивом")

    with zf:
        if "backup_data.json" not in zf.namelist():
            raise HTTPException(status_code=400, detail="В архиве отсутствует файл данных backup_data.json")

        try:
            raw_json = zf.read("backup_data.json").decode("utf-8")
            backup_data = json.loads(raw_json)
        except Exception:
            raise HTTPException(status_code=400, detail="Не удалось прочитать JSON-данные из архива")

        categories_data = backup_data.get("categories")
        products_data = backup_data.get("products")

        if not isinstance(categories_data, list) or not isinstance(products_data, list):
            raise HTTPException(status_code=400, detail="Некорректная структура разделов или товаров в резервной копии")

        # 1. Проверяем безопасность путей внутри uploads/ (защита от Zip Slip)
        upload_entries = []
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        for member in zf.infolist():
            if member.is_dir():
                continue
            norm_name = member.filename.replace("\\", "/")
            if norm_name.startswith("uploads/"):
                rel_subpath = norm_name[len("uploads/"):]
                if not rel_subpath or rel_subpath.startswith("/") or ".." in rel_subpath.split("/"):
                    raise HTTPException(status_code=400, detail="Обнаружен небезопасный путь внутри архива")
                target_path = os.path.abspath(os.path.join(abs_upload_dir, rel_subpath))
                if not target_path.startswith(abs_upload_dir + os.sep):
                    raise HTTPException(status_code=400, detail="Недопустимый путь файла в архиве")
                upload_entries.append((member, target_path))

        # 2. Полная замена категорий и товаров в БД в одной транзакции
        try:
            db.query(models.Product).delete()
            db.query(models.Category).delete()
            db.flush()

            for c in categories_data:
                db.add(
                    models.Category(
                        id=c.get("id"),
                        name=str(c["name"]).strip(),
                        icon=str(c.get("icon") or "watch").strip(),
                        subcategories=c.get("subcategories") if isinstance(c.get("subcategories"), list) else [],
                        sort_order=int(c.get("sort_order") or 0),
                    )
                )

            for p in products_data:
                db.add(
                    models.Product(
                        id=p.get("id"),
                        sku=str(p["sku"]).strip(),
                        group_id=(p.get("group_id") or "").strip() or None,
                        color_name=(p.get("color_name") or "").strip() or None,
                        category=str(p["category"]).strip(),
                        subcategory=(p.get("subcategory") or "").strip() or None,
                        name=str(p["name"]).strip(),
                        specs=str(p.get("specs") or "").strip(),
                        description=p.get("description"),
                        mechanism=p.get("mechanism"),
                        case_material=p.get("case_material"),
                        warranty=p.get("warranty") or "12 месяцев",
                        attributes=p.get("attributes"),
                        icon=str(p.get("icon") or "⌚").strip(),
                        image=(p.get("image") or "").strip() or None,
                        retail_price=float(p.get("retail_price") or 0.0),
                        wholesale_price=float(p.get("wholesale_price") or 0.0),
                        old_retail_price=float(p["old_retail_price"]) if p.get("old_retail_price") else None,
                        old_wholesale_price=float(p["old_wholesale_price"]) if p.get("old_wholesale_price") else None,
                        promo_label=(p.get("promo_label") or "").strip() or None,
                        min_wholesale_qty=int(p.get("min_wholesale_qty") or 5),
                        stock=int(p.get("stock") or 0),
                    )
                )


            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Ошибка восстановления базы данных: {str(e)}")

        # 3. Полностью перезаписываем папку uploads/ фотографиями из архива
        if os.path.exists(abs_upload_dir):
            for entry_name in os.listdir(abs_upload_dir):
                entry_path = os.path.join(abs_upload_dir, entry_name)
                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
                else:
                    os.remove(entry_path)
        else:
            os.makedirs(abs_upload_dir, exist_ok=True)

        for member, target_path in upload_entries:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with zf.open(member) as src, open(target_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    return {
        "ok": True,
        "categoriesCount": len(categories_data),
        "productsCount": len(products_data),
        "filesCount": len(upload_entries),
    }
