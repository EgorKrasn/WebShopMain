<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api.js'

const props = defineProps({
  userRole: {
    type: String,
    default: 'retail'
  },
  cartItems: {
    type: Array,
    default: () => []
  },
  searchQuery: {
    type: String,
    default: ''
  },
  selectedCategory: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['add-to-cart', 'reset-filters', 'select-product'])

const isLoadingProducts = ref(false)

const products = ref([
  {
    id: 101,
    sku: 'ST-8401',
    category: 'Наручные часы',
    name: 'Наручные кварцевые часы «Classic Steel»',
    specs: 'Корпус 40 мм • Сталь • Водозащита 5 ATM',
    description: 'Точный кварцевый механизм, чёткий контрастный циферблат и надёжный корпус.',
    mechanism: 'Кварцевый',
    caseMaterial: 'Нержавеющая сталь',
    warranty: '12 месяцев',
    icon: '⌚',
    image: '/images/1111.png',
    retailPrice: 185.00,
    wholesalePrice: 129.00,
    minWholesaleQty: 5
  },
  {
    id: 102,
    sku: 'ST-9120',
    category: 'Наручные часы',
    name: 'Механические часы с автоподзаводом «Chrono Master»',
    specs: 'Сапфировое стекло • Кожаный ремешок',
    description: 'Элегантные механические часы с автоподзаводом.',
    mechanism: 'Механика с автоподзаводом',
    caseMaterial: 'Сталь 316L / Кожа',
    warranty: '24 месяца',
    icon: '⌚',
    image: null,
    retailPrice: 340.00,
    wholesalePrice: 245.00,
    minWholesaleQty: 3
  },
  {
    id: 205,
    sku: 'ST-3310',
    category: 'Интерьерные и настенные',
    name: 'Настенные бесшумные часы «Nordic Loft 35 см»',
    specs: 'Плавный ход • Дерево и металл • Батарейка AA',
    description: 'Бесшумный плавный ход секундной стрелки для дома и офиса.',
    mechanism: 'Кварцевый плавный ход',
    caseMaterial: 'МДФ / Металл',
    warranty: '12 месяцев',
    icon: '🕰️',
    image: null,
    retailPrice: 74.00,
    wholesalePrice: 48.50,
    minWholesaleQty: 10
  },
  {
    id: 308,
    sku: 'ST-5504',
    category: 'Умные часы и браслеты',
    name: 'Смарт-часы спортивные «Pulse Pro AMOLED»',
    specs: 'GPS • Пульсометр • Защита IP68 • До 14 дней',
    description: 'Яркий AMOLED-дисплей, мониторинг активности и защита от влаги IP68.',
    mechanism: 'Электронный сенсорный',
    caseMaterial: 'Алюминиевый сплав / Силикон',
    warranty: '12 месяцев',
    icon: '📱',
    image: null,
    retailPrice: 260.00,
    wholesalePrice: 189.00,
    minWholesaleQty: 5
  }
])

onMounted(async () => {
  isLoadingProducts.value = true
  try {
    const serverProducts = await api.getProducts()
    if (Array.isArray(serverProducts) && serverProducts.length > 0) {
      products.value = serverProducts
    }
  } catch (err) {
    console.warn('Не удалось загрузить каталог с сервера, показаны локальные данные:', err.message)
  } finally {
    isLoadingProducts.value = false
  }
})

const filteredProducts = computed(() => {
  return products.value.filter((product) => {
    const matchesCategory =
      !props.selectedCategory || product.category === props.selectedCategory

    const query = props.searchQuery.trim().toLowerCase()
    const matchesSearch =
      !query ||
      product.name.toLowerCase().includes(query) ||
      product.sku.toLowerCase().includes(query) ||
      product.specs.toLowerCase().includes(query)

    return matchesCategory && matchesSearch
  })
})

const hasActiveFilters = computed(() => {
  return Boolean(props.selectedCategory || props.searchQuery.trim())
})

const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}

const getItemQtyInCart = (cartItems, productId) => {
  const found = cartItems.find((item) => item.id === productId)
  return found ? found.quantity : 0
}
</script>



<template>
  <section id="catalog" class="catalog-section">
    <div class="catalog-container">
      
      <!-- Шапка каталога -->
      <div class="catalog-header">
        <div>
          <h1 class="catalog-title">
            {{ selectedCategory || 'Каталог часов' }}
          </h1>
          <p class="catalog-subtitle">
            Найдено моделей: {{ filteredProducts.length }} • Оптово-розничные поставки по Беларуси
          </p>
        </div>

        <div class="price-legend" :class="{ wholesale: userRole === 'wholesale' }">
          <span v-if="userRole === 'wholesale'">🏢 Вы вошли как юрлицо — активны <strong>оптовые цены</strong></span>
          <span v-else>🛍️ Показаны розничные цены (опт доступен после регистрации по УНП)</span>
        </div>
      </div>

      <!-- Панель активных фильтров -->
      <div v-if="hasActiveFilters" class="active-filters-bar">
        <div class="filter-chips">
          <span v-if="selectedCategory" class="filter-chip">
            Категория: <strong>{{ selectedCategory }}</strong>
          </span>
          <span v-if="searchQuery.trim()" class="filter-chip">
            Поиск: <strong>«{{ searchQuery.trim() }}»</strong>
          </span>
        </div>
        <button type="button" class="btn-reset-filters" @click="emit('reset-filters')">
          ✕ Сбросить фильтры
        </button>
      </div>

      <!-- Если по запросу ничего не найдено -->
      <div v-if="filteredProducts.length === 0" class="empty-search-state">
        <div class="empty-search-icon">🔍</div>
        <h2>По вашему запросу ничего не найдено</h2>
        <p>Попробуйте изменить поисковый запрос или сбросить выбранную категорию.</p>
        <button type="button" class="btn-reset-main" @click="emit('reset-filters')">
          Показать все часы
        </button>
      </div>

      <!-- Адаптивная сетка карточек -->
      <div v-else class="products-grid">
        <article v-for="product in filteredProducts" :key="product.id" class="product-card">
          
          <!-- Клик по фото открывает подробную карточку -->
          <div class="image-placeholder" @click="emit('select-product', product)">
            <span class="sku-badge">Арт. {{ product.sku }}</span>
            <span class="category-tag">{{ product.category }}</span>
            
            <img 
              v-if="product.image" 
              :src="product.image" 
              :alt="product.name" 
              class="product-photo"
            />
            <div v-else class="placeholder-center">
              <span class="placeholder-icon">{{ product.icon }}</span>
              <span class="placeholder-text">Фото товара</span>
              <span class="placeholder-hint">400 × 400 px</span>
            </div>
          </div>

          <!-- Информация о товаре -->
          <div class="card-body">
            <!-- Клик по названию тоже открывает подробную карточку -->
            <h2 class="product-title" @click="emit('select-product', product)">
              {{ product.name }}
            </h2>
            <p class="product-specs">{{ product.specs }}</p>

            <!-- Блок цен (розница + опт) -->
            <div class="price-box">
              <template v-if="userRole === 'wholesale'">
                <div class="main-price-row">
                  <span class="main-price wholesale">{{ formatPrice(product.wholesalePrice) }} BYN</span>
                  <span class="price-badge wholesale">Опт</span>
                </div>
                <div class="secondary-price-row">
                  Розница: <span class="crossed">{{ formatPrice(product.retailPrice) }} BYN</span>
                </div>
              </template>

              <template v-else>
                <div class="main-price-row">
                  <span class="main-price">{{ formatPrice(product.retailPrice) }} BYN</span>
                  <span class="price-badge">Розница</span>
                </div>
                <div class="secondary-price-row">
                  Опт (от {{ product.minWholesaleQty }} шт.): <strong>{{ formatPrice(product.wholesalePrice) }} BYN</strong>
                </div>
              </template>
            </div>

            <!-- Кнопка добавления в корзину -->
            <button 
              type="button" 
              class="btn-add-cart"
              :class="{ 'in-cart': getItemQtyInCart(cartItems, product.id) > 0 }"
              @click="emit('add-to-cart', product)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <circle cx="9" cy="21" r="1"></circle>
                <circle cx="20" cy="21" r="1"></circle>
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
              </svg>
              <span v-if="getItemQtyInCart(cartItems, product.id) > 0">
                В корзине ({{ getItemQtyInCart(cartItems, product.id) }} шт.) • +1
              </span>
              <span v-else>В корзину</span>
            </button>
          </div>

        </article>
      </div>

    </div>
  </section>
</template>



<style scoped>
<style scoped>
.catalog-section {
  width: 100%;
  padding: 40px 32px 48px;
}

/* Центрированный контейнер витрины с аккуратными полями по бокам (как на WB) */
.catalog-container {
  max-width: 1440px;
  margin: 0 auto;
  width: 100%;
}

/* Шапка каталога */
.catalog-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  background-color: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(8px);
  padding: 18px 22px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}

.catalog-title {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
}

.catalog-subtitle {
  font-size: 14px;
  color: #475569;
  margin-top: 4px;
}

.price-legend {
  padding: 10px 16px;
  border-radius: 12px;
  background-color: #f1f5f9;
  color: #334155;
  font-size: 13px;
  border: 1px solid #cbd5e1;
}

.price-legend.wholesale {
  background-color: #0f172a;
  color: #A3D2F9;
  border-color: #0f172a;
}

/* Сетка товаров на компьютере */
.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

/* Карточка товара */
.product-card {
  background-color: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  min-width: 0; /* Защита от растягивания карточки длинным текстом на телефоне */
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.14);
}

.image-placeholder {
  position: relative;
  height: 210px;
  background-color: #ffffff; /* Чистый белый фон, чтобы сливался с белым фоном фото часов */
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px; /* Внутренний отступ картинки от всех границ карточки */
  overflow: hidden;
  cursor: pointer;
}

.product-photo {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Вписывает часы целиком без обрезки краёв */
  display: block;
}

.sku-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: rgba(15, 23, 42, 0.8);
  color: #f8fafc;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 7px;
}

.category-tag {
  position: absolute;
  bottom: 8px;
  left: 10px;
  right: 10px;
  width: fit-content;
  max-width: calc(100% - 20px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  background-color: rgba(255, 255, 255, 0.92);
  color: #334155;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}

.placeholder-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #64748b;
  text-align: center;
}

.placeholder-icon {
  font-size: 42px;
  opacity: 0.75;
}

.placeholder-text {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
}

.placeholder-hint {
  font-size: 11px;
  color: #94a3b8;
}

/* Контент карточки */
.card-body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.35;
}

.product-specs {
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

/* Блок цен */
.price-box {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.main-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  flex-wrap: wrap;
}

.main-price {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.main-price.wholesale {
  color: #0284c7;
}

.price-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 6px;
  background-color: #f1f5f9;
  color: #475569;
}

.price-badge.wholesale {
  background-color: #A3D2F9;
  color: #0f172a;
}

.secondary-price-row {
  font-size: 12px;
  color: #64748b;
}

.crossed {
  text-decoration: line-through;
  color: #94a3b8;
}

/* Кнопка В корзину */
.btn-add-cart {
  margin-top: 6px;
  height: 42px;
  width: 100%;
  border: none;
  border-radius: 12px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn-add-cart:hover {
  background-color: #7cc0f8;
}

.btn-add-cart:active {
  transform: scale(0.98);
}

.btn-add-cart.in-cart {
  background-color: #0f172a;
  color: #A3D2F9;
}

.btn-add-cart.in-cart:hover {
  background-color: #1e293b;
}

/* Панель активных фильтров */
.active-filters-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 18px;
  padding: 10px 16px;
  background-color: #0f172a;
  color: #f8fafc;
  border-radius: 12px;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  background-color: #1e293b;
  color: #A3D2F9;
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 8px;
}

.btn-reset-filters {
  background-color: #A3D2F9;
  color: #0f172a;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-reset-filters:hover {
  background-color: #82c2f7;
}

/* Блок «Ничего не найдено» */
.empty-search-state {
  background-color: rgba(255, 255, 255, 0.85);
  border-radius: 18px;
  padding: 48px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.empty-search-icon {
  font-size: 44px;
}

.empty-search-state h2 {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.empty-search-state p {
  font-size: 14px;
  color: #64748b;
}

.btn-reset-main {
  margin-top: 8px;
  padding: 11px 22px;
  border: none;
  border-radius: 12px;
  background-color: #0f172a;
  color: #A3D2F9;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}



/* Мобильная версия: аккуратные боковые поля 10px и строго 2 карточки в ряд */
@media (max-width: 680px) {
  .catalog-section {
    padding: 14px 10px 32px;
  }

  .catalog-header {
    padding: 12px 14px;
    margin-bottom: 14px;
    border-radius: 12px;
  }

  .catalog-title {
    font-size: 18px;
  }

  .catalog-subtitle {
    font-size: 12px;
  }

  .price-legend {
    font-size: 12px;
    padding: 8px 12px;
  }

  /* Строго 2 карточки в ширину экрана */
  .products-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .product-card {
    border-radius: 12px;
  }

  .image-placeholder {
    height: 150px;
    padding: 8px;
  }

  .sku-badge {
    top: 8px;
    left: 8px;
    font-size: 10px;
    padding: 2px 6px;
  }

  .category-tag {
    bottom: 6px;
    left: 8px;
    right: 8px;
    font-size: 10px;
    padding: 2px 6px;
  }

  .placeholder-icon {
    font-size: 32px;
  }

  .placeholder-text {
    font-size: 11px;
  }

  .placeholder-hint {
    display: none;
  }

  .card-body {
    padding: 10px;
    gap: 6px;
  }

  .product-title {
    font-size: 13px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .product-specs {
    font-size: 11px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .main-price {
    font-size: 16px;
  }

  .price-badge {
    font-size: 10px;
    padding: 2px 5px;
  }

  .secondary-price-row {
    font-size: 11px;
  }

  .btn-add-cart {
    height: 36px;
    font-size: 12px;
    border-radius: 10px;
    padding: 0 8px;
  }

  .btn-add-cart svg {
    width: 15px;
    height: 15px;
  }
}



</style>