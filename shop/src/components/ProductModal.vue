<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  product: {
    type: Object,
    default: null
  },
  userRole: {
    type: String,
    default: 'retail'
  },
  cartItems: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'add-to-cart'])

const quantity = ref(1)

watch(
  () => props.product,
  (newProduct) => {
    if (newProduct) {
      quantity.value = 1
    }
  }
)

const isWholesale = computed(() => props.userRole === 'wholesale')

const unitPrice = computed(() => {
  if (!props.product) return 0
  return isWholesale.value ? props.product.wholesalePrice : props.product.retailPrice
})

const totalPrice = computed(() => {
  return unitPrice.value * quantity.value
})

const qtyInCart = computed(() => {
  if (!props.product) return 0
  const found = props.cartItems.find((item) => item.id === props.product.id)
  return found ? found.quantity : 0
})

const decreaseQty = () => {
  if (quantity.value >= 2) {
    quantity.value -= 1
  }
}

const increaseQty = () => {
  quantity.value += 1
}

const setWholesaleMinQty = () => {
  if (props.product?.minWholesaleQty) {
    quantity.value = props.product.minWholesaleQty
  }
}

const handleAdd = () => {
  if (!props.product) return
  emit('add-to-cart', { product: props.product, quantity: quantity.value })
  emit('close')
}

const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}
</script>




<template>
  <Transition name="modal-fade">
    <div v-if="product" class="modal-backdrop" @click.self="emit('close')">
      <div class="modal-card" role="dialog" aria-modal="true" :aria-label="product.name">
        
        <!-- Верхняя панель окна -->
        <div class="modal-top-bar">
          <div class="top-badges">
            <span class="sku-pill">Арт. {{ product.sku }}</span>
            <span class="cat-pill">{{ product.category }}</span>
          </div>
          <button type="button" class="close-btn" @click="emit('close')" aria-label="Закрыть окно">
            ✕
          </button>
        </div>

        <div class="modal-content">
          <!-- Левая колонка: Крупное фото или заглушка -->
          <div class="media-column">
            <div class="large-image-box">
              <img 
                v-if="product.image" 
                :src="product.image" 
                :alt="product.name" 
                class="large-photo"
              />
              <div v-else class="large-placeholder">
                <span class="large-icon">{{ product.icon || '⌚' }}</span>
                <span class="large-text">Фото товара</span>
                <span class="large-hint">Рекомендуемый размер: 800 × 800 px</span>
              </div>
            </div>

            <div class="stock-status">
              <span class="status-dot"></span>
              <span>В наличии на складе в Минске • Доставка по РБ</span>
            </div>
          </div>

          <!-- Правая колонка: Описание, характеристики, цена и количество -->
          <div class="info-column">
            <h2 class="product-title">{{ product.name }}</h2>

            <p class="product-description">
              {{ product.description || 'Надёжная модель из каталога «СандринТайм». Поставляется в фирменной упаковке с официальной гарантией и полным комплектом документов для розничных и оптовых покупателей.' }}
            </p>

            <!-- Таблица характеристик -->
            <div class="specs-block">
              <h3 class="specs-heading">Характеристики</h3>
              <dl class="specs-list">
                <div class="spec-row">
                  <dt>Кратко:</dt>
                  <dd>{{ product.specs }}</dd>
                </div>
                <div v-if="product.mechanism" class="spec-row">
                  <dt>Механизм:</dt>
                  <dd>{{ product.mechanism }}</dd>
                </div>
                <div v-if="product.caseMaterial" class="spec-row">
                  <dt>Материал:</dt>
                  <dd>{{ product.caseMaterial }}</dd>
                </div>
                <div v-if="product.warranty" class="spec-row">
                  <dt>Гарантия:</dt>
                  <dd>{{ product.warranty }}</dd>
                </div>
                <div class="spec-row">
                  <dt>Мин. оптовая партия:</dt>
                  <dd>от {{ product.minWholesaleQty }} шт.</dd>
                </div>
              </dl>
            </div>

            <!-- Блок цены -->
            <div class="price-panel">
              <template v-if="isWholesale">
                <div class="price-main-line">
                  <span class="current-price wholesale">{{ formatPrice(product.wholesalePrice) }} BYN</span>
                  <span class="role-tag wholesale">Оптовая цена / шт.</span>
                </div>
                <div class="price-sub-line">
                  Розничная цена: <span class="crossed">{{ formatPrice(product.retailPrice) }} BYN</span>
                </div>
              </template>

              <template v-else>
                <div class="price-main-line">
                  <span class="current-price">{{ formatPrice(product.retailPrice) }} BYN</span>
                  <span class="role-tag">Розничная цена / шт.</span>
                </div>
                <div class="price-sub-line">
                  Опт (от {{ product.minWholesaleQty }} шт. для юрлиц): <strong>{{ formatPrice(product.wholesalePrice) }} BYN</strong>
                </div>
              </template>
            </div>

            <!-- Выбор количества и кнопка добавления -->
            <div class="purchase-controls">
              <div class="qty-row">
                <div class="qty-selector">
                  <button type="button" class="qty-btn" @click="decreaseQty" aria-label="Уменьшить">−</button>
                  <input 
                    v-model.number="quantity" 
                    type="number" 
                    min="1" 
                    class="qty-input"
                    aria-label="Количество"
                  />
                  <button type="button" class="qty-btn" @click="increaseQty" aria-label="Увеличить">+</button>
                </div>

                <button 
                  type="button" 
                  class="btn-min-lot"
                  @click="setWholesaleMinQty"
                  title="Выбрать минимальную оптовую партию"
                >
                  Опт-лот ({{ product.minWholesaleQty }} шт.)
                </button>
              </div>

              <button type="button" class="btn-add-confirm" @click="handleAdd">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <circle cx="9" cy="21" r="1"></circle>
                  <circle cx="20" cy="21" r="1"></circle>
                  <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                </svg>
                <span>Добавить в корзину • {{ formatPrice(totalPrice) }} BYN</span>
              </button>

              <p v-if="qtyInCart > 0" class="already-in-cart">
                Сейчас в вашей корзине уже есть {{ qtyInCart }} шт. этой модели.
              </p>
            </div>

          </div>
        </div>

      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.68);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 280;
  overflow-y: auto;
}

.modal-card {
  width: 100%;
  max-width: 860px;
  background-color: #ffffff;
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
  color: #0f172a;
  margin: auto;
}

/* Верхняя полоса */
.modal-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 22px;
  background-color: #0f172a;
  color: #ffffff;
}

.top-badges {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sku-pill {
  background-color: #1e293b;
  color: #A3D2F9;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 8px;
}

.cat-pill {
  font-size: 12px;
  color: #cbd5e1;
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.14);
}

/* Основная сетка модального окна */
.modal-content {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 24px;
  padding: 24px;
}

/* Левая колонка */
.media-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.large-image-box {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 16px;
  background: linear-gradient(145deg, #e2e8f0 0%, #f1f5f9 100%);
  border: 1.5px dashed #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.large-photo {
  width: 100%;
  height: 100%;
  object-fit: contain; 
  display: block;
}

.large-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
  padding: 16px;
}

.large-icon {
  font-size: 64px;
  opacity: 0.8;
}

.large-text {
  font-size: 15px;
  font-weight: 700;
  color: #475569;
}

.large-hint {
  font-size: 12px;
  color: #94a3b8;
}

.stock-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  background-color: #f8fafc;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.status-dot {
  width: 8px;
  height: 8px;
border-radius: 50%;
background-color: #22c55e;
flex-shrink: 0;
}
/* Правая колонка */
.info-column {
display: flex;
flex-direction: column;
gap: 14px;
}
.product-title {
font-size: 22px;
font-weight: 800;
color: #0f172a;
line-height: 1.25;
}
.product-description {
font-size: 14px;
color: #475569;
line-height: 1.5;
}
/* Характеристики */
.specs-block {
background-color: #f8fafc;
border: 1px solid #e2e8f0;
border-radius: 12px;
padding: 12px 14px;
}
.specs-heading {
font-size: 13px;
font-weight: 700;
color: #0f172a;
margin-bottom: 8px;
}
.specs-list {
display: flex;
flex-direction: column;
gap: 6px;
}
.spec-row {
display: flex;
justify-content: space-between;
gap: 12px;
font-size: 13px;
border-bottom: 1px dashed #e2e8f0;
padding-bottom: 4px;
}
.spec-row:last-child {
border-bottom: none;
padding-bottom: 0;
}
.spec-row dt {
color: #64748b;
flex-shrink: 0;
}
.spec-row dd {
color: #0f172a;
font-weight: 600;
text-align: right;
}
/* Панель цены */
.price-panel {
padding: 12px 14px;
border-radius: 12px;
background-color: rgba(163, 210, 249, 0.25);
border: 1px solid #A3D2F9;
}
.price-main-line {
display: flex;
align-items: center;
justify-content: space-between;
gap: 10px;
flex-wrap: wrap;
}
.current-price {
font-size: 24px;
font-weight: 800;
color: #0f172a;
}
.current-price.wholesale {
color: #0284c7;
}
.role-tag {
font-size: 12px;
font-weight: 700;
padding: 4px 10px;
border-radius: 8px;
background-color: #ffffff;
color: #334155;
}
.role-tag.wholesale {
background-color: #0f172a;
color: #A3D2F9;
}
.price-sub-line {
font-size: 13px;
color: #475569;
margin-top: 4px;
}
.crossed {
text-decoration: line-through;
color: #94a3b8;
}
/* Выбор количества и покупка */
.purchase-controls {
margin-top: auto;
display: flex;
flex-direction: column;
gap: 10px;
}
.qty-row {
display: flex;
align-items: center;
gap: 10px;
}
.qty-selector {
display: inline-flex;
align-items: center;
border: 1.5px solid #cbd5e1;
border-radius: 12px;
overflow: hidden;
height: 44px;
background-color: #ffffff;
}
.qty-btn {
width: 38px;
height: 100%;
border: none;
background: transparent;
font-size: 18px;
font-weight: 700;
color: #0f172a;
cursor: pointer;
}
.qty-btn:hover {
background-color: #A3D2F9;
}
.qty-input {
width: 52px;
height: 100%;
border: none;
text-align: center;
font-size: 15px;
font-weight: 700;
color: #0f172a;
outline: none;
}
/* Убираем стрелки у input type="number" */
.qty-input::-webkit-outer-spin-button,
.qty-input::-webkit-inner-spin-button {
-webkit-appearance: none;
margin: 0;
}
.btn-min-lot {
height: 44px;
padding: 0 14px;
border-radius: 12px;
border: 1.5px solid #cbd5e1;
background-color: #f8fafc;
color: #334155;
font-size: 13px;
font-weight: 700;
cursor: pointer;
transition: all 0.2s ease;
}
.btn-min-lot:hover {
border-color: #0284c7;
background-color: rgba(163, 210, 249, 0.25);
color: #0f172a;
}
.btn-add-confirm {
height: 48px;
width: 100%;
border: none;
border-radius: 12px;
background-color: #A3D2F9;
color: #0f172a;
font-size: 15px;
font-weight: 800;
display: inline-flex;
align-items: center;
justify-content: center;
gap: 8px;
cursor: pointer;
transition: background-color 0.2s ease, transform 0.1s ease;
}
.btn-add-confirm:hover {
background-color: #7cc0f8;
}
.btn-add-confirm:active {
transform: scale(0.99);
}
.already-in-cart {
font-size: 12px;
color: #0284c7;
font-weight: 600;
text-align: center;
}
/* Анимация */
.modal-fade-enter-active,
.modal-fade-leave-active {
transition: opacity 0.22s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
opacity: 0;
}
/* Адаптация под мобильные телефоны */
@media (max-width: 740px) {
.modal-content {
grid-template-columns: 1fr;
padding: 16px;
gap: 16px;
}
.large-image-box {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 16px;
  background-color: #ffffff; /* Чистый белый фон под фото */
  border: 1.5px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px; /* Аккуратный отступ от границ рамки */
  overflow: hidden;
}
.product-title {
font-size: 18px;
}
.current-price {
font-size: 20px;
}
}
</style>