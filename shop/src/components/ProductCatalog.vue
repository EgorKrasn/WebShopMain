<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as XLSX from 'xlsx'
import { api, resolveImageUrl } from '../services/api.js'
import {
  Building2,
  FileSpreadsheet,
  Search,
  X,
  ShoppingCart,
  Watch,
  ChevronLeft,
  ChevronRight,
  ArrowUp
} from 'lucide-vue-next'





const props = defineProps({
  products: {
    type: Array,
    default: () => []
  },
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
  },
  selectedSubcategory: {
    type: String,
    default: ''
  }
})


const emit = defineEmits([
  'add-to-cart',
  'update-qty',
  'set-qty',
  'reset-filters',
  'select-product',
  'products-loaded',
  'update-search'
])


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
    emit('products-loaded', products.value)
    isLoadingProducts.value = false
  }
})

const filteredProducts = computed(() => {
  return (props.products || []).filter((product) => {
    const matchesCategory =
      !props.selectedCategory || product.category === props.selectedCategory

    const matchesSubcategory =
      !props.selectedSubcategory || product.subcategory === props.selectedSubcategory

    const query = props.searchQuery.trim().toLowerCase()
    const matchesSearch =
      !query ||
      product.name.toLowerCase().includes(query) ||
      product.sku.toLowerCase().includes(query) ||
      (product.specs || '').toLowerCase().includes(query)

    return matchesCategory && matchesSubcategory && matchesSearch
  })
})

const hasActiveFilters = computed(() => {
  return Boolean(props.selectedCategory || props.selectedSubcategory || props.searchQuery.trim())
})

// --- ПАГИНАЦИЯ И СИНХРОНИЗАЦИЯ С URL (?page=2) ---
const route = useRoute()
const router = useRouter()
const ITEMS_PER_PAGE = 24 // Кратно 4 колонкам на ПК и 2 на смартфоне

const currentPage = computed(() => {
  const raw = Number(route.query.page)
  return Number.isInteger(raw) && raw > 0 ? raw : 1
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredProducts.value.length / ITEMS_PER_PAGE))
})

// Если в URL передали ?page=99, а страниц всего 3 — берём безопасную страницу
const safePage = computed(() => {
  return Math.min(currentPage.value, totalPages.value)
})

const paginatedProducts = computed(() => {
  const start = (safePage.value - 1) * ITEMS_PER_PAGE
  return filteredProducts.value.slice(start, start + ITEMS_PER_PAGE)
})

// Формируем список номеров страниц с многоточием (например: [1, '...', 4, 5, 6, '...', 12])
const visiblePages = computed(() => {
  const total = totalPages.value
  const current = safePage.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages = [1]
  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

const goToPage = (page, shouldScroll = true) => {
  const target = Math.min(Math.max(1, Number(page) || 1), totalPages.value)
  const nextQuery = { ...route.query }

  if (target === 1) {
    delete nextQuery.page // Для 1-й страницы держим чистый URL без ?page=1
  } else {
    nextQuery.page = String(target)
  }

  router.push({ query: nextQuery })

  if (shouldScroll) {
    const el = document.getElementById('catalog')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
}

// При изменении категории, подкатегории или поискового запроса сбрасываемся на 1-ю страницу
watch(
  [() => props.selectedCategory, () => props.selectedSubcategory, () => props.searchQuery],
  () => {
    if (route.query.page) {
      const nextQuery = { ...route.query }
      delete nextQuery.page
      router.replace({ query: nextQuery })
    }
  }
)

// Если товаров стало меньше и текущая ?page=N оказалась за пределами totalPages — корректируем URL
watch([totalPages, currentPage], ([total, curr]) => {
  if (curr > total && route.query.page) {
    const nextQuery = { ...route.query }
    if (total <= 1) {
      delete nextQuery.page
    } else {
      nextQuery.page = String(total)
    }
    router.replace({ query: nextQuery })
  }
})

// --- КНОПКА «НАВЕРХ» ---
const showScrollTop = ref(false)

const handleWindowScroll = () => {
  showScrollTop.value = window.scrollY > 450
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  window.addEventListener('scroll', handleWindowScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleWindowScroll)
})



const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}

const getItemQtyInCart = (cartItems, productId) => {
  const found = cartItems.find((item) => item.id === productId)
  return found ? found.quantity : 0
}

const handleDirectQtyInput = (productId, event) => {
  const parsed = parseInt(event.target.value, 10)
  if (isNaN(parsed) || parsed <= 0) {
    // Если ввели 0 или стёрли значение — удаляем товар из корзины (вернётся кнопка «В корзину»)
    emit('set-qty', { id: productId, quantity: 0 })
  } else {
    emit('set-qty', { id: productId, quantity: parsed })
  }
}

const exportPriceListToExcel = () => {
  if (!props.products || props.products.length === 0) return

  // 1. Формируем строки таблицы с понятными заголовками
  const rows = props.products.map((p) => ({
    'Артикул': p.sku || '',
    'Категория': p.category || '',
    'Наименование': p.name || '',
    'Цвет': p.colorName || '—',
    'Характеристики': p.specs || '',
    'Оптовая цена (BYN)': Number(p.wholesalePrice || 0),
    'Мин. партия (шт.)': Number(p.minWholesaleQty || 1),
    'Остаток на складе (шт.)': Number(p.stock ?? 0),
    'РРЦ / Розница (BYN)': Number(p.retailPrice || 0)
  }))

  // 2. Создаём лист Excel из массива объектов
  const worksheet = XLSX.utils.json_to_sheet(rows)

  // 3. Автоматически рассчитываем ширину каждой колонки под самый длинный текст
  const headers = Object.keys(rows[0])
  worksheet['!cols'] = headers.map((header) => {
    const maxDataLength = rows.reduce((maxLen, row) => {
      const cellText = String(row[header] ?? '')
      return Math.max(maxLen, cellText.length)
    }, header.length)

    // Добавляем запас +4 символа, чтобы текст не упирался в границы ячеек
    return { wch: maxDataLength + 4 }
  })

  // 4. Создаём книгу Excel и скачиваем её как настоящий .xlsx файл
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Прайс-лист Сандринтайм')

  const today = new Date().toISOString().slice(0, 10)
  XLSX.writeFile(workbook, `Price_SandrinTime_${today}.xlsx`)
}


</script>



<template>
  <section id="catalog" class="catalog-section">
    <div class="catalog-container">
      
      <!-- Шапка каталога -->
      <div class="catalog-header">
        <div class="catalog-header-top">
          <div>
            <h1 class="catalog-title">
              {{ selectedSubcategory || selectedCategory || 'Каталог часов' }}
            </h1>

            <p class="catalog-subtitle">
              Найдено моделей: {{ filteredProducts.length }} • Оптово-розничные поставки по Беларуси
            </p>
          </div>

          <div v-if="userRole === 'wholesale'" class="wholesale-header-actions">
            <div class="wholesale-badge">
              <Building2 :size="16" style="vertical-align: -3px; margin-right: 4px;" />
              Вы вошли как юрлицо — активны <strong>оптовые цены</strong>
            </div>
            <button
              type="button"
              class="btn-download-price"
              @click="exportPriceListToExcel"
              title="Скачать актуальный оптовый прайс-лист в формате Excel (.xlsx)"
            >
              <FileSpreadsheet :size="16" />
              <span>Скачать прайс (Excel)</span>
            </button>
          </div>
        </div>

        <!-- Строка поиска для ПК -->
        <div class="catalog-search-wrapper">
          <div class="catalog-search-bar">
            <Search :size="19" :stroke-width="2.2" class="search-lead-icon" />
            <input
              :value="searchQuery"
              type="text"
              class="catalog-search-input"
              placeholder="Найти часы по названию, бренду, характеристикам или артикулу..."
              @input="emit('update-search', $event.target.value)"
            />
            <button
              v-if="searchQuery"
              type="button"
              class="catalog-search-clear"
              aria-label="Очистить поиск"
              @click="emit('update-search', '')"
            >
              <X :size="15" />
            </button>
          </div>
        </div>
      </div>

      <!-- Панель активных фильтров -->
      <div v-if="hasActiveFilters" class="active-filters-bar">
        <div class="filter-chips">
          <span v-if="selectedCategory" class="filter-chip">
            Категория: <strong>{{ selectedCategory }}</strong>
          </span>
          <span v-if="selectedSubcategory" class="filter-chip">
            Подкатегория: <strong>{{ selectedSubcategory }}</strong>
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
        <div class="empty-search-icon">
          <Search :size="44" :stroke-width="1.6" color="#64748b" />
        </div>
        <h2>По вашему запросу ничего не найдено</h2>
        <p>Попробуйте изменить поисковый запрос или сбросить выбранную категорию.</p>
        <button type="button" class="btn-reset-main" @click="emit('reset-filters')">
          Показать все часы
        </button>
      </div>

      <!-- Адаптивная сетка карточек -->
      <div v-else class="products-grid">
        <article
          v-for="product in paginatedProducts"
          :key="product.id"
          class="product-card"
          :class="{ 'out-of-stock': (product.stock ?? 0) <= 0 }"
        >
          <!-- Клик по фото открывает подробную карточку -->
          <div class="image-placeholder" @click="emit('select-product', product)">
            <span class="sku-badge">Арт. {{ product.sku }}</span>
            <span class="category-tag">{{ product.category }}</span>
            
            <img 
              v-if="product.image" 
              :src="resolveImageUrl(product.image)" 
              :alt="product.name" 
              class="product-photo"
            />

            <div v-else class="placeholder-center">
              <span class="placeholder-icon">
                <Watch :size="40" :stroke-width="1.6" color="#94a3b8" />
              </span>
              <span class="placeholder-text">Фото товара</span>
              <span class="placeholder-hint">400 × 400 px</span>
            </div>
          </div>

          <!-- Информация о товаре -->
          <div class="card-body">
            <h2 class="product-title" @click="emit('select-product', product)">
              {{ product.name }}
            </h2>
            <p class="product-specs">{{ product.specs }}</p>

            <!-- Блок цен (розница + опт) -->
            <div class="price-box">
              <template v-if="userRole === 'wholesale'">
                <div class="price-wholesale">{{ formatPrice(product.wholesalePrice) }} BYN</div>
                <div class="price-retail-sub">Розница: {{ formatPrice(product.retailPrice) }} BYN</div>
              </template>
              <template v-else>
                <div class="price-retail">{{ formatPrice(product.retailPrice) }} BYN</div>
              </template>
            </div>

            <!-- Счётчик количества (если товар уже в корзине) или кнопка «В корзину» -->
            <div v-if="getItemQtyInCart(cartItems, product.id) > 0" class="catalog-qty-control">
              <button
                type="button"
                class="cat-qty-btn"
                aria-label="Уменьшить количество"
                @click="emit('update-qty', { id: product.id, delta: -1 })"
              >
                −
              </button>

              <input
                type="number"
                min="1"
                class="cat-qty-input"
                :value="getItemQtyInCart(cartItems, product.id)"
                aria-label="Количество в корзине"
                @change="handleDirectQtyInput(product.id, $event)"
              />

              <button
                type="button"
                class="cat-qty-btn"
                aria-label="Увеличить количество"
                @click="emit('update-qty', { id: product.id, delta: 1 })"
              >
                +
              </button>
            </div>

            <button
              v-else
              type="button"
              class="btn-add-cart"
              :disabled="(product.stock ?? 0) <= 0"
              @click="emit('add-to-cart', product)"
            >
              <span v-if="(product.stock ?? 0) <= 0">Нет в наличии</span>
              <template v-else>
                <ShoppingCart :size="17" :stroke-width="2.2" />
                <span>В корзину</span>
              </template>
            </button>
          </div>
        </article>
      </div>

      <!-- Панель пагинации -->
      <nav
        v-if="filteredProducts.length > ITEMS_PER_PAGE"
        class="pagination-bar"
        aria-label="Навигация по страницам каталога"
      >
        <div class="pagination-info">
          Показано
          <strong>
            {{ (safePage - 1) * ITEMS_PER_PAGE + 1 }}–{{ Math.min(safePage * ITEMS_PER_PAGE, filteredProducts.length) }}
          </strong>
          из <strong>{{ filteredProducts.length }}</strong>
        </div>

        <div class="pagination-controls">
          <button
            type="button"
            class="page-btn page-nav-btn"
            :disabled="safePage <= 1"
            aria-label="Предыдущая страница"
            @click="goToPage(safePage - 1)"
          >
            <ChevronLeft :size="18" />
            <span class="nav-btn-label">Назад</span>
          </button>

          <template v-for="(item, idx) in visiblePages" :key="idx">
            <span v-if="item === '...'" class="page-ellipsis">…</span>
            <button
              v-else
              type="button"
              class="page-btn"
              :class="{ active: item === safePage }"
              @click="goToPage(item)"
            >
              {{ item }}
            </button>
          </template>

          <button
            type="button"
            class="page-btn page-nav-btn"
            :disabled="safePage >= totalPages"
            aria-label="Следующая страница"
            @click="goToPage(safePage + 1)"
          >
            <span class="nav-btn-label">Вперёд</span>
            <ChevronRight :size="18" />
          </button>
        </div>
      </nav>

    </div>

    <!-- Плавающая кнопка «Наверх» -->
    <Teleport to="body">
      <Transition name="fade-up">
        <button
          v-if="showScrollTop"
          type="button"
          class="sandrin-scroll-top-btn"
          aria-label="Прокрутить наверх"
          title="Наверх"
          @click="scrollToTop"
        >
          <ArrowUp :size="20" :stroke-width="2.4" />
          <span class="scroll-top-text">Наверх</span>
        </button>
      </Transition>
    </Teleport>

  </section>
</template>




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
  padding: 38px 16px 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-photo {
  max-width: 100%;
  max-height: 150px;
  object-fit: contain;
  position: relative;
  z-index: 1;
}

.sku-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 3;
  background-color: rgba(15, 23, 42, 0.85);
  color: #f8fafc;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 7px;
  white-space: nowrap;
}

.category-tag {
  position: absolute;
  bottom: 8px;
  left: 10px;
  right: 10px;
  z-index: 3;
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

.price-retail,
.price-wholesale {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.2;
}

.price-wholesale {
  color: #0284c7;
}

.price-retail-sub {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
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
    height: 168px;
    padding: 32px 10px 28px;
  }

  .product-photo {
    max-height: 112px;
  }

  .sku-badge {
    top: 7px;
    left: 7px;
    font-size: 9.5px;
    padding: 2px 6px;
    border-radius: 6px;
  }

  .category-tag {
    bottom: 6px;
    left: 7px;
    right: 7px;
    max-width: calc(100% - 14px);
    font-size: 9.5px;
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

    .catalog-qty-control {
    height: 36px;
    border-radius: 10px;
    grid-template-columns: 36px 1fr 36px;
  }

  .cat-qty-btn {
    font-size: 16px;
  }

  .cat-qty-input {
    font-size: 13px;
  }

  .price-retail,
  .price-wholesale {
    font-size: 16px;
  }

  .price-retail-sub {
    font-size: 11px;
  }

}

/* Компактный счётчик количества на карточке в каталоге */
.catalog-qty-control {
  margin-top: 6px;
  height: 42px;
  width: 100%;
  border-radius: 12px;
  background-color: #0f172a;
  color: #A3D2F9;
  display: grid;
  grid-template-columns: 44px 1fr 44px;
  align-items: center;
  overflow: hidden;
  border: 1.5px solid #0f172a;
}

.cat-qty-btn {
  height: 100%;
  border: none;
  background: transparent;
  color: #A3D2F9;
  font-size: 19px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.cat-qty-btn:hover {
  background-color: #A3D2F9;
  color: #0f172a;
}

.cat-qty-btn:active {
  transform: scale(0.95);
}

.cat-qty-input {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  color: #ffffff;
  text-align: center;
  font-size: 15px;
  font-weight: 800;
  outline: none;
}

/* Убираем стандартные стрелки у input type="number" */
.cat-qty-input::-webkit-outer-spin-button,
.cat-qty-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.cat-qty-input[type="number"] {
  -moz-appearance: textfield;
}

.wholesale-header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-download-price {
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #0284c7;
  background-color: #ffffff;
  color: #0284c7;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.18s ease;
}

.btn-download-price:hover {
  background-color: #0284c7;
  color: #ffffff;
}

/* Приглушённый вид карточки при нулевом остатке */
.product-card.out-of-stock {
  opacity: 0.62;
  background-color: #f8fafc;
}

.product-card.out-of-stock:hover {
  opacity: 0.85;
}

.product-card.out-of-stock img {
  filter: grayscale(70%);
}


.btn-add-cart:disabled {
  background-color: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.btn-add-cart:disabled:hover {
  background-color: #e2e8f0;
  transform: none;
}

.catalog-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  background-color: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  padding: 20px 24px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
}

.catalog-header-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.catalog-search-wrapper {
  width: 100%;
}

.catalog-search-bar {
  width: 100%;
  height: 48px;
  background-color: #ffffff;
  border: 2px solid #cbd5e1;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.catalog-search-bar:focus-within {
  border-color: #0f172a;
  box-shadow: 0 0 0 3px rgba(163, 210, 249, 0.45);
}

.search-lead-icon {
  color: #64748b;
  flex-shrink: 0;
}

.catalog-search-bar:focus-within .search-lead-icon {
  color: #0f172a;
}

.catalog-search-input {
  flex: 1;
  width: 100%;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: #0f172a;
}

.catalog-search-input::placeholder {
  color: #94a3b8;
}

.catalog-search-clear {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: none;
  background-color: #f1f5f9;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.catalog-search-clear:hover {
  background-color: #0f172a;
  color: #ffffff;
}

/* На телефонах поиск уже есть в верхней шапке Navbar, поэтому дублировать его здесь не нужно */
@media (max-width: 960px) {
  .catalog-search-wrapper {
    display: none;
  }
}




</style>

<style>
/* --- ПАГИНАЦИЯ КАТАЛОГА --- */
.pagination-bar {
  margin-top: 28px;
  padding: 16px 20px;
  background-color: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.pagination-info {
  font-size: 13px;
  color: #475569;
}

.pagination-info strong {
  color: #0f172a;
}

.pagination-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.page-btn {
  min-width: 38px;
  height: 38px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #0f172a;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.16s ease;
}

.page-btn:hover:not(:disabled) {
  border-color: #0f172a;
  background-color: #f1f5f9;
}

.page-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
}

.page-btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.page-ellipsis {
  padding: 0 4px;
  color: #64748b;
  font-weight: 700;
  user-select: none;
}

@media (max-width: 680px) {
  .pagination-bar {
    flex-direction: column;
    align-items: center;
    padding: 14px 12px;
    margin-top: 20px;
  }

  .nav-btn-label {
    display: none;
  }

  .page-btn {
    min-width: 34px;
    height: 34px;
    padding: 0 8px;
    font-size: 13px;
  }
}

/* --- КНОПКА «НАВЕРХ» --- */
.sandrin-scroll-top-btn {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 999;
  height: 46px;
  padding: 0 18px;
  border-radius: 999px;
  border: 1.5px solid rgba(163, 210, 249, 0.55);
  background-color: #0f172a;
  color: #A3D2F9;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  cursor: pointer;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.32);
  transition: transform 0.18s ease, background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.sandrin-scroll-top-btn:hover {
  background-color: #A3D2F9;
  color: #0f172a;
  border-color: #0f172a;
  transform: translateY(-3px);
}

.sandrin-scroll-top-btn:active {
  transform: scale(0.96);
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(14px);
}

@media (max-width: 960px) {
  .sandrin-scroll-top-btn {
    right: 16px;
    bottom: calc(78px + env(safe-area-inset-bottom, 0px));
    width: 44px;
    height: 44px;
    padding: 0;
  }

  .sandrin-scroll-top-btn .scroll-top-text {
    display: none;
  }
}
</style>
