from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
import schemas
import security
from database import engine, get_db, SessionLocal


# Создаём таблицы в SQLite при запуске
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Интернет-магазина ООО «Сандринтайм»")

# Разрешаем запросы с фронтенда Vue (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Заполнение каталога стартовыми товарами, если база пустая
def seed_initial_products():
    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            initial_products = [
                models.Product(
                    id=101,
                    sku="ST-8401",
                    category="Наручные часы",
                    name="Наручные кварцевые часы «Classic Steel»",
                    specs="Корпус 40 мм • Сталь • Водозащита 5 ATM",
                    description="Надёжная классическая модель из каталога «Сандринтайм» с точным кварцевым механизмом.",
                    mechanism="Кварцевый",
                    case_material="Нержавеющая сталь",
                    warranty="12 месяцев",
                    icon="⌚",
                    image="/images/1111.png",
                    retail_price=185.00,
                    wholesale_price=129.00,
                    min_wholesale_qty=5,
                ),
                models.Product(
                    id=102,
                    sku="ST-9120",
                    category="Наручные часы",
                    name="Механические часы с автоподзаводом «Chrono Master»",
                    specs="Сапфировое стекло • Кожаный ремешок",
                    description="Элегантные механические часы с прозрачной задней крышкой и автоподзаводом.",
                    mechanism="Механика с автоподзаводом",
                    case_material="Сталь 316L / Кожа",
                    warranty="24 месяца",
                    icon="⌚",
                    image=None,
                    retail_price=340.00,
                    wholesale_price=245.00,
                    min_wholesale_qty=3,
                ),
                models.Product(
                    id=205,
                    sku="ST-3310",
                    category="Интерьерные и настенные",
                    name="Настенные бесшумные часы «Nordic Loft 35 см»",
                    specs="Плавный ход • Дерево и металл • Батарейка AA",
                    description="Бесшумный плавный ход секундной стрелки — идеально для спальни, гостиной или офиса.",
                    mechanism="Кварцевый плавный ход",
                    case_material="МДФ / Металл",
                    warranty="12 месяцев",
                    icon="🕰️",
                    image=None,
                    retail_price=74.00,
                    wholesale_price=48.50,
                    min_wholesale_qty=10,
                ),
                models.Product(
                    id=308,
                    sku="ST-5504",
                    category="Умные часы и браслеты",
                    name="Смарт-часы спортивные «Pulse Pro AMOLED»",
                    specs="GPS • Пульсометр • Защита IP68 • До 14 дней",
                    description="Яркий AMOLED-дисплей, мониторинг активности и защита от влаги IP68.",
                    mechanism="Электронный сенсорный",
                    case_material="Алюминиевый сплав / Силикон",
                    warranty="12 месяцев",
                    icon="📱",
                    image=None,
                    retail_price=260.00,
                    wholesale_price=189.00,
                    min_wholesale_qty=5,
                ),
            ]
            db.add_all(initial_products)
            db.commit()
    finally:
        db.close()


seed_initial_products()


# 1. Получить весь каталог товаров
@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    items = db.query(models.Product).all()
    return [
        {
            "id": p.id,
            "sku": p.sku,
            "category": p.category,
            "name": p.name,
            "specs": p.specs,
            "description": p.description,
            "mechanism": p.mechanism,
            "caseMaterial": p.case_material,
            "warranty": p.warranty,
            "icon": p.icon,
            "image": p.image,
            "retailPrice": p.retail_price,
            "wholesalePrice": p.wholesale_price,
            "minWholesaleQty": p.min_wholesale_qty,
        }
        for p in items
    ]


# Вспомогательная функция формирования ответа с пользователем и JWT-токеном
def build_auth_response(user: models.User):
    token = security.create_access_token(user_id=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "role": user.role,
            "email": user.email,
            "name": user.company_name if user.role == "wholesale" else user.full_name,
            "contactName": user.full_name,
            "unp": user.unp,
        }
    }


# 2. Регистрация (выдаёт JWT-токен сразу после создания аккаунта)
@app.post("/api/auth/register")
def register_user(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже зарегистрирован")

    new_user = models.User(
        role=payload.role,
        email=payload.email,
        hashed_password=pwd_context.hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        unp=payload.unp if payload.role == "wholesale" else None,
        company_name=payload.company_name if payload.role == "wholesale" else None,
        legal_address=payload.legal_address if payload.role == "wholesale" else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return build_auth_response(new_user)


# 3. Вход в аккаунт (проверяет пароль и выдаёт JWT-токен)
@app.post("/api/auth/login")
def login_user(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    return build_auth_response(user)

# Смена статуса аккаунта (физлицо <-> юрлицо/ИП по УНП)
@app.patch("/api/auth/role")
def switch_user_role(
    payload: schemas.SwitchRoleRequest,
    current_user: models.User = Depends(security.get_current_user_required),
    db: Session = Depends(get_db)
):
    if payload.role not in ("retail", "wholesale"):
        raise HTTPException(status_code=400, detail="Некорректный тип аккаунта")

    if payload.role == "wholesale":
        if not payload.company_name or not payload.company_name.strip():
            raise HTTPException(status_code=400, detail="Укажите наименование организации или ИП")
        current_user.role = "wholesale"
        current_user.unp = payload.unp
        current_user.company_name = payload.company_name.strip()
    else:
        current_user.role = "retail"

    db.commit()
    db.refresh(current_user)

    # Возвращаем обновлённый профиль и новый JWT-токен с актуальной ролью
    return build_auth_response(current_user)



# 4. Создание новой заявки (привязывает к пользователю из JWT-токена, если он вошёл)
@app.post("/api/orders")
def create_order(
    payload: schemas.OrderCreateRequest,
    current_user: models.User | None = Depends(security.get_current_user_optional),
    db: Session = Depends(get_db)
):
    is_europost = payload.delivery.method == "europost"
    initial_status = "europost_pending" if is_europost else "processing"

    new_order = models.Order(
        number="TEMP",
        user_id=current_user.id if current_user else None,
        role=current_user.role if current_user else payload.role,
        status=initial_status,
        recipient_name=payload.recipient.full_name,
        recipient_phone=payload.recipient.phone,
        delivery_method=payload.delivery.method,
        delivery_city=payload.delivery.city,
        delivery_office=payload.delivery.office,
        company_name=current_user.company_name if current_user else None,
        unp=current_user.unp if current_user else None,
        comment=payload.comment,
        products_total_byn=payload.products_total_byn,
    )
    db.add(new_order)
    db.flush()

    new_order.number = f"СТ-{new_order.id:04d}"

    for item in payload.items:
        db.add(
            models.OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                sku=item.sku,
                name=item.name,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        )

    db.commit()
    db.refresh(new_order)

    return {
        "id": new_order.id,
        "number": new_order.number,
        "status": new_order.status,
        "createdAt": new_order.created_at.strftime("%d.%m.%Y %H:%M"),
    }


# 5. Защищённое получение заявок только для авторизованного владельца JWT-токена
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

