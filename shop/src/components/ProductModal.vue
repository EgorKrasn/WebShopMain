<script setup>
import { ref, computed, watch } from 'vue'
import { resolveImageUrl } from '../services/api.js'
import {
  Share2,
  Check,
  X,
  Watch,
  ShoppingCart
} from 'lucide-vue-next'

import { useBackdropClose } from '../composables/useBackdropClose.js'



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
  },
  // Заготовка под глобальные настройки названий полей из админки в будущем
  fieldLabels: {
    type: Object,
    default: () => ({
      specs: 'Кратко',
      mechanism: 'Механизм',
      caseMaterial: 'Материал',
      warranty: 'Гарантия',
      minWholesaleQty: 'Мин. оптовая партия'
    })
  }
})

const emit = defineEmits(['close', 'add-to-cart', 'select-variant'])
const { onBackdropMouseDown, onBackdropMouseUp } = useBackdropClose(() => emit('close'))

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

const hasColorVariants = computed(() => {
  return Array.isArray(props.product?.variants) && props.product.variants.length > 1
})

// Динамический список характеристик: берёт массив из БД (от админа) или собирает из базовых полей
const displayAttributes = computed(() => {
  if (!props.product) return []

  if (Array.isArray(props.product.attributes) && props.product.attributes.length > 0) {
    return props.product.attributes.filter((attr) => attr.label && attr.value)
  }

  const list = []
  if (props.product.specs) {
    list.push({ label: props.fieldLabels.specs, value: props.product.specs })
  }
  if (props.product.mechanism) {
    list.push({ label: props.fieldLabels.mechanism, value: props.product.mechanism })
  }
  if (props.product.caseMaterial) {
    list.push({ label: props.fieldLabels.caseMaterial, value: props.product.caseMaterial })
  }
  if (props.product.warranty) {
    list.push({ label: props.fieldLabels.warranty, value: props.product.warranty })
  }
  return list
})

const decreaseQty = () => {
  if (quantity.value >= 2) {
    quantity.value -= 1
  }
}



const setWholesaleMinQty = () => {
  if (props.product?.minWholesaleQty) {
    quantity.value = props.product.minWholesaleQty
  }
}

const handleVariantClick = (variantId) => {
  if (variantId === props.product?.id) return
  emit('select-variant', variantId)
}

const handleAdd = () => {
  if (!props.product) return
  emit('add-to-cart', { product: props.product, quantity: quantity.value })
  emit('close')
}

const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}

const linkCopied = ref(false)

const copyProductLink = async () => {
  try {
    await navigator.clipboard.writeText(window.location.href)
    linkCopied.value = true
    setTimeout(() => {
      linkCopied.value = false
    }, 2000)
  } catch (err) {
    console.warn('Не удалось скопировать ссылку:', err)
  }
}

const availableStock = computed(() => {
  return Number(props.product?.stock ?? 0)
})

const isOutOfStock = computed(() => {
  return availableStock.value <= 0
})

// Обновите increaseQty, чтобы нельзя было выбрать больше, чем есть на складе:
const increaseQty = () => {
  if (quantity.value < availableStock.value) {
    quantity.value += 1
  }
}


</script>

<template>
  <Transition name="modal-fade">
    <div
      v-if="product"
      class="modal-backdrop"
      @mousedown.self="onBackdropMouseDown"
      @mouseup.self="onBackdropMouseUp"
    >

      <div class="modal-card" role="dialog" aria-modal="true" :aria-label="product.name">
        
        <!-- Верхняя панель окна -->
        <div class="modal-top-bar">
          <div class="top-badges">
            <span class="sku-pill">Арт. {{ product.sku }}</span>
            <span class="cat-pill">{{ product.category }}</span>
            <button
              type="button"
              class="copy-link-btn"
              :class="{ copied: linkCopied }"
              @click="copyProductLink"
              title="Скопировать прямую ссылку на этот цвет"
            >
              <Check v-if="linkCopied" :size="13" />
              <Share2 v-else :size="13" />
              <span>{{ linkCopied ? 'Ссылка скопирована' : 'Поделиться' }}</span>
            </button>
          </div>
          <button type="button" class="close-btn" @click="emit('close')" aria-label="Закрыть окно">
            <X :size="18" />
          </button>

        </div>

        <div class="modal-content">
          <!-- Левая колонка: Крупное фото или заглушка + остаток на складе -->
          <div class="media-column">
            <div class="large-image-box">
              <img 
                v-if="product.image" 
                :src="resolveImageUrl(product.image)" 
                :alt="product.name" 
                class="large-photo"
              />
              <div v-else class="large-placeholder">
                <span class="large-icon">
                  <Watch :size="58" :stroke-width="1.5" color="#94a3b8" />
                </span>
                <span class="large-text">Фото товара</span>
                <span class="large-hint">Рекомендуемый размер: 800 × 800 px</span>
              </div>

            </div>

            <div
              class="stock-status"
              :class="{
                'out-of-stock': isOutOfStock,
                'low-stock': availableStock > 0 && availableStock < 10
              }"
            >
              <span class="status-dot"></span>
              <span v-if="isOutOfStock">Нет в наличии (под заказ)</span>
              <span v-else>В наличии на складе: <strong>{{ availableStock }} шт.</strong> • Доставка по РБ</span>
            </div>
          </div>

          <!-- Правая колонка: Описание, цвета, характеристики, цена и количество -->
          <div class="info-column">
            <h2 class="product-title">{{ product.name }}</h2>

            <!-- Блок выбора цвета (как на Wildberries) -->
            <div v-if="hasColorVariants" class="color-variants-block">
              <div class="color-label-row">
                <span class="color-label">Цвет:</span>
                <strong class="color-current-name">{{ product.colorName || 'Выбранный вариант' }}</strong>
              </div>

              <div class="color-swatches-grid">
                <button
                  v-for="variant in product.variants"
                  :key="variant.id"
                  type="button"
                  class="color-swatch-card"
                  :class="{
                    active: variant.id === product.id,
                    'out-of-stock': variant.stock !== undefined && variant.stock <= 0
                  }"
                  :title="(variant.stock !== undefined && variant.stock <= 0) ? `${variant.colorName} (нет в наличии)` : variant.colorName"
                  @click="handleVariantClick(variant.id)"
                >


                  <img
                    v-if="variant.image"
                    :src="resolveImageUrl(variant.image)"
                    :alt="variant.colorName"
                    class="swatch-img"
                  />
                  <div v-else class="swatch-placeholder">
                    <Watch :size="18" :stroke-width="1.8" color="#64748b" />
                    <span class="swatch-fallback-text">{{ variant.colorName }}</span>
                  </div>

                </button>
              </div>
            </div>

            <p class="product-description">
              {{ product.description || 'Надёжная модель из каталога «СандринТайм». Поставляется в фирменной упаковке с официальной гарантией и полным комплектом документов для розничных и оптовых покупателей.' }}
            </p>

            <!-- Таблица характеристик (динамическая) -->
            <div class="specs-block">
              <h3 class="specs-heading">Характеристики</h3>
              <dl class="specs-list">
                <div
                  v-for="(attr, index) in displayAttributes"
                  :key="index"
                  class="spec-row"
                >
                  <dt>{{ attr.label }}:</dt>
                  <dd>{{ attr.value }}</dd>
                </div>

                <div v-if="isWholesale" class="spec-row">
                  <dt>{{ fieldLabels.minWholesaleQty }}:</dt>
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
                    :max="availableStock || 1"
                    class="qty-input"
                    aria-label="Количество"
                  />
                  <button type="button" class="qty-btn" @click="increaseQty" aria-label="Увеличить">+</button>
                </div>

                <button 
                  v-if="isWholesale"
                  type="button" 
                  class="btn-min-lot"
                  @click="setWholesaleMinQty"
                  title="Выбрать минимальную оптовую партию"
                >
                  Опт-лот ({{ product.minWholesaleQty }} шт.)
                </button>
              </div>

              <button
                type="button"
                class="btn-add-confirm"
                :disabled="isOutOfStock"
                @click="handleAdd"
              >
                <ShoppingCart :size="19" :stroke-width="2.2" />
                <span v-if="isOutOfStock">Нет в наличии</span>
                <span v-else>Добавить в корзину • {{ formatPrice(totalPrice) }} BYN</span>
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
display: inline-flex; 
align-items: center; 
justify-content: center;

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
background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
border: 1.5px solid #e2e8f0;
display: flex;
align-items: center;
justify-content: center;
padding: 14px;
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
/* Блок выбора цвета (как на WB) */
.color-variants-block {
display: flex;
flex-direction: column;
gap: 8px;
}
.color-label-row {
display: flex;
align-items: center;
gap: 6px;
font-size: 13px;
}
.color-label {
color: #64748b;
}
.color-current-name {
color: #0f172a;
font-weight: 700;
}
.color-swatches-grid {
display: flex;
flex-wrap: wrap;
gap: 8px;
}
.color-swatch-card {
width: 64px;
height: 76px;
border-radius: 12px;
border: 2px solid #e2e8f0;
background-color: #ffffff;
padding: 4px;
cursor: pointer;
overflow: hidden;
display: flex;
align-items: center;
justify-content: center;
transition: all 0.18s ease;
}
.color-swatch-card:hover {
border-color: #93c5fd;
transform: translateY(-2px);
}
.color-swatch-card.active {
border-color: #0284c7;
background-color: rgba(163, 210, 249, 0.18);
box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2);
}
.swatch-img {
width: 100%;
height: 100%;
object-fit: contain;
border-radius: 8px;
display: block;
}
/* Базовая заглушка для миниатюры без фото */
.swatch-placeholder {
width: 100%;
height: 100%;
border-radius: 8px;
background: linear-gradient(145deg, #f1f5f9 0%, #e2e8f0 100%);
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
padding: 4px;
gap: 3px;
text-align: center;
}
.swatch-icon {
font-size: 20px;
line-height: 1;
}
.swatch-fallback-text {
font-size: 9px;
font-weight: 700;
color: #475569;
line-height: 1.15;
display: -webkit-box;
-webkit-line-clamp: 2;
-webkit-box-orient: vertical;
overflow: hidden;
word-break: break-word;
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
background-color: #ffffff;
padding: 16px;
}
.product-title {
font-size: 18px;
}
.current-price {
font-size: 20px;
}
}

.copy-link-btn {
  background-color: rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex; 
  align-items: center; 
  gap: 5px;
}

.copy-link-btn:hover {
  background-color: rgba(163, 210, 249, 0.25);
  border-color: #A3D2F9;
  color: #ffffff;
}

.copy-link-btn.copied {
  background-color: #22c55e;
  border-color: #22c55e;
  color: #ffffff;
}

.stock-status.low-stock .status-dot {
  background-color: #f59e0b;
}

.stock-status.out-of-stock {
  background-color: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.stock-status.out-of-stock .status-dot {
  background-color: #ef4444;
}

.btn-add-confirm:disabled {
  background-color: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}
/* Приглушённый вид миниатюры цвета, которого нет в наличии */
.color-swatch-card.out-of-stock {
  opacity: 0.45;
  background-color: #f8fafc;
}

.color-swatch-card.out-of-stock .swatch-img {
  filter: grayscale(80%);
}

.color-swatch-card.out-of-stock:hover {
  opacity: 0.72;
}

.color-swatch-card.out-of-stock.active {
  opacity: 0.85;
}


</style>