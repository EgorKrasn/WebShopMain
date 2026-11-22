<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { api, resolveImageUrl } from '../services/api.js'
import * as XLSX from 'xlsx'
import {
  ArrowLeft,
  X,
  Building2,
  Package,
  Watch,
  Trash2,
  AlertTriangle,
  FileSpreadsheet,
  ArrowRight,
  Handshake,
  Store
} from 'lucide-vue-next'
import ConsentCheckbox from './ConsentCheckbox.vue'



const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  items: {
    type: Array,
    default: () => []
  },
  userRole: {
    type: String,
    default: 'retail'
  },
  currentUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'update-qty', 'set-qty', 'remove-item', 'clear-cart', 'checkout'])


const step = ref('cart')
const personalDataConsent = ref(false)

// Состояние предупредительного окна об оплате через Европочту
const isWarningModalOpen = ref(false)
const pendingOrderPayload = ref(null)

const orderForm = reactive({
  deliveryMethod: 'europost', // 'europost' или 'pickup'
  fullName: '',
  phone: '',
  city: '',
  europostOffice: '',
  companyName: '',
  unp: '',
  comment: ''
})

const formError = ref('')

const isWholesale = computed(() => props.userRole === 'wholesale')
// Для юрлиц выбор Европочты отключаем — доставка обсуждается с менеджером
const isEuropost = computed(() => !isWholesale.value && orderForm.deliveryMethod === 'europost')
const getMinWholesaleQty = (item) => Number(item.minWholesaleQty || 1)

const getMissingWholesaleQty = (item) => {
  if (!isWholesale.value) return 0
  const minQty = getMinWholesaleQty(item)
  return item.quantity < minQty ? minQty - item.quantity : 0
}

const hasUnmetWholesaleMin = computed(() => {
  if (!isWholesale.value) return false
  return props.items.some((item) => getMissingWholesaleQty(item) > 0)
})

const fillToWholesaleMin = (item) => {
  emit('set-qty', { id: item.id, quantity: getMinWholesaleQty(item) })
}


const syncUserData = () => {
  if (props.currentUser) {
    orderForm.fullName = props.currentUser.contactName || props.currentUser.name || ''
    if (props.currentUser.role === 'wholesale') {
      orderForm.companyName = props.currentUser.name || ''
      orderForm.unp = props.currentUser.unp || ''
    }
  }
}

watch(
  () => props.isOpen,
  (opened) => {
    if (opened) {
      step.value = 'cart'
      formError.value = ''
      isWarningModalOpen.value = false
      personalDataConsent.value = false
      syncUserData()
    }
  }
)

const getUnitPrice = (item) => {
  return isWholesale.value ? item.wholesalePrice : item.retailPrice
}

const totalCount = computed(() => {
  return props.items.reduce((sum, item) => sum + item.quantity, 0)
})

const retailTotal = computed(() => {
  return props.items.reduce((sum, item) => sum + item.retailPrice * item.quantity, 0)
})

const productsTotal = computed(() => {
  return props.items.reduce((sum, item) => sum + getUnitPrice(item) * item.quantity, 0)
})

const wholesaleSavings = computed(() => {
  return isWholesale.value ? retailTotal.value - productsTotal.value : 0
})


const deliveryCost = computed(() => 0)

const grandTotal = computed(() => {
  return productsTotal.value + deliveryCost.value
})

const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}

const goToCheckout = () => {
  if (hasUnmetWholesaleMin.value) return
  formError.value = ''
  syncUserData()
  step.value = 'checkout'
}

const prepareOrder = () => {
  formError.value = ''

  if (!orderForm.fullName.trim()) {
    formError.value = isEuropost.value
      ? 'Укажите Фамилию, Имя и Отчество полностью'
      : 'Укажите ваше имя'
    return
  }

  // Для Европочты требуем полные ФИО (минимум 3 слова) и отделение
  if (isEuropost.value) {
    const nameParts = orderForm.fullName.trim().split(/\s+/)
    if (!(nameParts.length >= 3)) {
      formError.value = 'Для Европочты укажите Фамилию, Имя и Отчество полностью (как в паспорте)'
      return
    }
    if (!orderForm.city.trim() || !orderForm.europostOffice.trim()) {
      formError.value = 'Укажите город и номер/адрес отделения Европочты'
      return
    }
  }

  if (!orderForm.phone.trim()) {
    formError.value = 'Укажите актуальный номер телефона'
    return
  }

  if (!personalDataConsent.value) {
    formError.value = 'Подтвердите согласие на обработку персональных данных'
    return
  }


  const payload = {
    personal_data_consent: personalDataConsent.value,
    role: props.userRole,
    recipient: {
      full_name: orderForm.fullName.trim(),
      phone: orderForm.phone.trim()
    },
    ...(isWholesale.value && {
      legal_entity: {
        company_name: orderForm.companyName.trim(),
        unp: orderForm.unp.replace(/\D/g, '')
      }
    }),
    delivery: isWholesale.value
      ? {
          method: 'manager',
          address: 'Обсуждается с менеджером',
          cost_byn: 0
        }
      : isEuropost.value
        ? {
            method: 'europost',
            city: orderForm.city.trim(),
            office: orderForm.europostOffice.trim(),
            cost_byn: 0
          }
        : {
            method: 'pickup',
            address: 'Рынок «ЭКСПОБЕЛ», пав. 218/219, 1 этаж, 4 ряд',
            cost_byn: 0
          },
    payment_method: isWholesale.value ? 'manager' : isEuropost.value ? 'europost_cod' : 'pickup_cod',

    comment: orderForm.comment.trim() || null,
    products_total_byn: Number(productsTotal.value.toFixed(2)),
    total_byn: Number(grandTotal.value.toFixed(2)),
    items: props.items.map((item) => ({
      product_id: item.id,
      sku: item.sku,
      name: item.name,
      quantity: item.quantity,
      unit_price: getUnitPrice(item)
    }))
  }

  // Если выбрана Европочта — показываем предупредительное окно об оплате и паспорте
  if (isEuropost.value) {
    pendingOrderPayload.value = payload
    isWarningModalOpen.value = true
    return
  }

  // Если самовывоз — сразу отправляем заявку
  console.log('Отправка заявки (Самовывоз) на Python API (/api/orders):', payload)
  emit('checkout', payload)
}

const confirmFinalOrder = () => {
  if (!pendingOrderPayload.value) return
  console.log('Отправка заявки (Европочта) на Python API (/api/orders):', pendingOrderPayload.value)
  const submittedPayload = pendingOrderPayload.value
  isWarningModalOpen.value = false
  pendingOrderPayload.value = null
  emit('checkout', submittedPayload)
}

function addToCart(product, variant) {
  const cartKey = variant ? `${product.id}_${variant.id}` : `${product.id}`;
  // Сохраняйте в объект корзины fields: variant_id, color_name, sku и image выбранного варианта.
}


const exportCartToExcel = () => {
  if (!isWholesale.value || props.items.length === 0) return

  const today = new Date().toLocaleDateString('ru-RU')
  const fileDate = new Date().toISOString().slice(0, 10)

  const sheetRows = [
    ['ПРЕДВАРИТЕЛЬНАЯ СМЕТА ЗАКАЗА', '', '', 'Дата:', today],
    [],
    ['ПОСТАВЩИК:', 'ООО «Сандринтайм»', '', 'ПОКУПАТЕЛЬ:', props.currentUser?.name || '—'],
    ['УНП поставщика:', '690876665', '', 'УНП покупателя:', props.currentUser?.unp || '—'],
    ['Юридический адрес:', '223053, Минский р-н, Боровлянский с/с, д. Боровая, д. 7, ком. 1', '', 'Контактное лицо:', props.currentUser?.contactName || '—'],
    ['Фактический адрес:', 'Минский р-н, пересечение Логойского тракта и МКАД, ТРЦ «Экспобел», пав. 218/219', '', 'Email:', props.currentUser?.email || '—'],
    ['Телефоны:', '+375 (29) 651-19-83, +375 (29) 000-00-00', '', '', ''],
    [],
    ['№', 'Артикул', 'Наименование товара', 'Кол-во (шт.)', 'Оптовая цена (BYN)', 'Сумма (BYN)']
  ]

  props.items.forEach((item, index) => {
    const qty = Number(item.quantity || 0)
    const price = Number(getUnitPrice(item) || 0)
    sheetRows.push([
      index + 1,
      item.sku || '',
      item.name || '',
      qty,
      price,
      Number((qty * price).toFixed(2))
    ])
  })

  sheetRows.push([])
  sheetRows.push(['', '', '', '', 'ИТОГО ПО СМЕТЕ (BYN):', Number(productsTotal.value.toFixed(2))])

  const worksheet = XLSX.utils.aoa_to_sheet(sheetRows)

  const colCount = 6
  const colWidths = []
  for (let c = 0; c < colCount; c++) {
    let maxLen = 12
    for (let r = 0; r < sheetRows.length; r++) {
      const cellVal = sheetRows[r]?.[c]
      if (cellVal !== undefined && cellVal !== null) {
        maxLen = Math.max(maxLen, String(cellVal).length)
      }
    }
    colWidths.push({ wch: maxLen + 4 })
  }
  worksheet['!cols'] = colWidths

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Смета заказа')
  XLSX.writeFile(workbook, `Smeta_SandrinTime_${fileDate}.xlsx`)
}

</script>


<template>
  <Transition name="fade">
    <div v-if="isOpen" class="cart-backdrop" @click="emit('close')"></div>
  </Transition>

  <Transition name="slide-right">
    <aside v-if="isOpen" class="cart-drawer">
      <div class="cart-header">
        <div class="cart-header-left">
          <button v-if="step === 'checkout'" type="button" class="btn-back-step" @click="step = 'cart'">
            <ArrowLeft :size="16" />
          </button>

          <h2 class="cart-title">{{ step === 'cart' ? 'Корзина' : 'Оформление заявки' }}</h2>
          <span v-if="step === 'cart'" class="cart-count-pill">{{ totalCount }} шт.</span>
        </div>

        <div class="cart-header-actions">
          <button
            v-if="step === 'cart' && items.length > 0"
            type="button"
            class="btn-clear-cart"
            @click="emit('clear-cart')"
            title="Удалить все товары из корзины"
          >
            Очистить
          </button>
          <button type="button" class="cart-close" @click="emit('close')" aria-label="Закрыть">
            <X :size="18" />
          </button>

        </div>
      </div>


      <div class="price-mode-banner" :class="{ wholesale: isWholesale }">
        <span v-if="isWholesale" style="display: inline-flex; align-items: center; gap: 6px;">
          <Building2 :size="15" /> Активен <strong>оптовый прайс</strong> (УНП) • Оплата при получении
        </span>
        <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
          <Package :size="15" /> Доставка <strong>Европочтой</strong> или <strong>Самовывоз</strong> • Оплата при получении
        </span>
      </div>


      <div v-if="items.length === 0" class="cart-empty">
        <div class="empty-icon"><Watch :size="48" :stroke-width="1.5" color="#94a3b8" /></div>

        <h3>В корзине пока пусто</h3>
        <p>Выберите наручные, настенные или умные часы в каталоге.</p>
        <button type="button" class="btn-back-catalog" @click="emit('close')">Перейти в каталог</button>
      </div>

      <div v-else-if="step === 'cart'" class="checkout-wrapper">
        <div class="cart-body">
          <ul class="cart-list">
            <li v-for="item in items" :key="item.id" class="cart-item">
              <div class="item-thumb">
                <img v-if="item.image" :src="resolveImageUrl(item.image)" :alt="item.name" class="item-thumb-img" />
                <span v-else><Watch :size="24" color="#0f172a" /></span>

              </div>
              <div class="item-details">
                <div class="item-top">
                  <div>
                    <span class="item-sku">Арт. {{ item.sku }}</span>
                    <h4 class="item-name">{{ item.name }}</h4>
                  </div>
                  <button type="button" class="item-remove" @click="emit('remove-item', item.id)" aria-label="Удалить">
                    <Trash2 :size="16" />
                  </button>

                </div>
                <div class="item-bottom">
                  <div v-if="getMissingWholesaleQty(item) > 0" class="wholesale-min-alert">
                    <span>Для опта добавьте ещё <strong>{{ getMissingWholesaleQty(item) }} шт.</strong></span>
                    <button type="button" class="btn-fill-min" @click="fillToWholesaleMin(item)">
                      Добить до {{ getMinWholesaleQty(item) }} шт.
                    </button>
                  </div>

                  <div class="qty-control">
                    <button type="button" class="qty-btn" @click="emit('update-qty', { id: item.id, delta: -1 })">−</button>
                    <span class="qty-value">{{ item.quantity }}</span>
                    <button type="button" class="qty-btn" @click="emit('update-qty', { id: item.id, delta: 1 })">+</button>
                  </div>
                  <div class="item-price-block">
                    <span v-if="isWholesale" class="item-old-price">{{ formatPrice(item.retailPrice * item.quantity) }} BYN</span>
                    <span class="item-current-price">{{ formatPrice(getUnitPrice(item) * item.quantity) }} BYN</span>
                    <span class="item-unit-note">{{ formatPrice(getUnitPrice(item)) }} BYN / шт.</span>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>
        <div class="cart-footer">
          <div v-if="hasUnmetWholesaleMin" class="footer-min-warning" style="display: flex; align-items: center; gap: 6px;">
            <AlertTriangle :size="16" style="flex-shrink: 0;" />
            <span>Чтобы оформить оптовую заявку, наберите минимальную партию по всем позициям.</span>
          </div>

          <div class="summary-row total">
            <span>Сумма товаров:</span>
            <span class="total-amount">{{ formatPrice(productsTotal) }} BYN</span>
          </div>

          <button
            v-if="isWholesale"
            type="button"
            class="btn-export-smeta"
            style="display: inline-flex; align-items: center; justify-content: center; gap: 6px;"
            @click="exportCartToExcel"
          >
            <FileSpreadsheet :size="16" />
            <span>Скачать смету (Excel)</span>
          </button>

          <button
            type="button"
            class="btn-checkout"
            style="display: inline-flex; align-items: center; justify-content: center; gap: 6px;"
            :disabled="hasUnmetWholesaleMin"
            @click="goToCheckout"
          >
            <span v-if="hasUnmetWholesaleMin">Не набрана мин. оптовая партия</span>
            <template v-else>
              <span>Перейти к оформлению</span>
              <ArrowRight :size="17" />
            </template>
          </button>
        </div>


      </div>

      <form v-else class="checkout-wrapper" @submit.prevent="prepareOrder">
        <div class="cart-body checkout-scroll">
          
          <!-- Для ЮРЛИЦ: предупредительная табличка вместо выбора доставки -->
          <div v-if="isWholesale" class="wholesale-delivery-notice">
            <div class="notice-icon"><Handshake :size="22" color="#0284c7" /></div>
            <div class="notice-content">
              <strong>Условия доставки и оплаты для юрлиц и ИП</strong>
              <p>Способы получения, сроки отгрузки и условия оплаты оптового заказа обсуждаются индивидуально с менеджером после получения заявки.</p>
            </div>
          </div>

          <!-- Для ФИЗЛИЦ: выбор способа получения (Европочта или Самовывоз) -->
          <div v-else class="form-section">
            <h3 class="section-heading">1. Способ получения заказа</h3>
            <div class="radio-cards">
              <label class="radio-card" :class="{ selected: orderForm.deliveryMethod === 'europost' }">
                <input type="radio" v-model="orderForm.deliveryMethod" value="europost" class="hidden-radio" />
                <div class="radio-info">
                  <span class="radio-title"><Package :size="15" style="vertical-align: -2px; margin-right: 4px;" /> Европочта (до отделения по РБ)</span>
                  <span class="radio-desc">Стоимость уточняется менеджером • Оплата при получении</span>
                </div>
                <span class="radio-check">{{ orderForm.deliveryMethod === 'europost' ? '●' : '○' }}</span>
              </label>

              <label class="radio-card" :class="{ selected: orderForm.deliveryMethod === 'pickup' }">
                <input type="radio" v-model="orderForm.deliveryMethod" value="pickup" class="hidden-radio" />
                <div class="radio-info">
                  <span class="radio-title"><Store :size="15" style="vertical-align: -2px; margin-right: 4px;" /> Самовывоз</span>
                  <span class="radio-desc">Рынок «ЭКСПОБЕЛ», пав. 218/219, 1 этаж, 4 ряд • Бесплатно</span>
                </div>
                <span class="radio-check">{{ orderForm.deliveryMethod === 'pickup' ? '●' : '○' }}</span>
              </label>
            </div>
          </div>

          <!-- Предупреждение в форме только для физлиц при выборе Европочты -->
          <div v-if="isEuropost" class="europost-alert">
            <div class="alert-icon"><AlertTriangle :size="20" color="#d97706" /></div>
            <div class="alert-text">
              <strong>Оплата и выдача через Европочту:</strong>
              <p>Оплата производится при получении посылки в отделении Европочты. Выдача строго по паспорту.</p>
            </div>
          </div>

          <!-- Контактные данные (для юрлица это единственный блок полей) -->
          <div class="form-section">
            <h3 class="section-heading">
              {{ isWholesale ? 'Контактная информация представителя' : isEuropost ? '2. Данные получателя (как в паспорте)' : '2. Контактные данные' }}
            </h3>
            <div class="field-group">
              <label>
                {{ isEuropost ? 'Фамилия, Имя и Отчество полностью *' : 'Контактное лицо (Имя или ФИО) *' }}
              </label>
              <input 
                v-model="orderForm.fullName" 
                type="text" 
                :placeholder="isEuropost ? 'Иванов Иван Иванович' : 'Иван Иванов'" 
                required 
              />
              <span v-if="isEuropost" class="field-note">
                Указывайте строго как в паспорте — выдача в отделении по документу.
              </span>
            </div>

            <div class="field-group">
              <label>Актуальный номер телефона *</label>
              <input 
                v-model="orderForm.phone" 
                type="tel" 
                placeholder="+375 (29) 123-45-67" 
                required 
              />
              <span v-if="isEuropost" class="field-note">
                На этот номер придут SMS-уведомления о прибытии посылки.
              </span>
            </div>
          </div>

          <!-- Поля отделения Европочты (только для физлиц при выборе Европочты) -->
          <div v-if="isEuropost" class="form-section">
            <h3 class="section-heading">3. Отделение Европочты</h3>
            <div class="field-group">
              <label>Город / населённый пункт *</label>
              <input v-model="orderForm.city" type="text" placeholder="Например: Минск, Логойск, Брест..." required />
            </div>
            <div class="field-group">
              <label>Номер и адрес отделения Европочты *</label>
              <input v-model="orderForm.europostOffice" type="text" placeholder="Например: ОПС №124, ул. Притыцкого, 29" required />
            </div>
          </div>

          <div class="form-section">
            <div class="field-group">
              <label>Комментарий к заявке</label>
              <input v-model="orderForm.comment" type="text" placeholder="Удобное время звонка или пожелания..." />
            </div>
          </div>
          <ConsentCheckbox v-model="personalDataConsent" />

          <div v-if="formError" class="checkout-error">{{ formError }}</div>
        </div>

        <div class="cart-footer">
          <div class="summary-row small">
            <span>Товары ({{ totalCount }} шт.):</span>
            <span>{{ formatPrice(productsTotal) }} BYN</span>
          </div>
          <div class="summary-row small">
            <span>{{ isWholesale ? 'Способ получения:' : isEuropost ? 'Пересылка Европочтой:' : 'Самовывоз:' }}</span>
            <span>{{ isWholesale ? 'Обсуждается с менеджером' : isEuropost ? 'Уточняется менеджером' : 'Бесплатно' }}</span>
          </div>
          <div class="summary-row total">
            <span>{{ isWholesale || isEuropost ? 'Сумма товаров:' : 'Итого при получении:' }}</span>
            <span class="total-amount">{{ formatPrice(productsTotal) }} BYN</span>
          </div>
          <button type="submit" class="btn-checkout">Оформить заявку</button>
        </div>
      </form>


      <div v-if="isWarningModalOpen" class="warning-overlay">
        <div class="warning-dialog">
          <div class="warning-badge"><Package :size="14" style="vertical-align: -2px; margin-right: 4px;" /> Условия оплаты Европочтой</div>
          <h3 class="warning-title">Подтверждение способа оплаты</h3>
          <p class="warning-body">
            Обратите внимание: <strong>оплата заказа осуществляется через Европочту</strong> при получении посылки в выбранном отделении.
          </p>
          <ul class="warning-checklist">
            <li><strong>Получатель:</strong> {{ orderForm.fullName }}</li>
            <li><strong>SMS-уведомления на:</strong> {{ orderForm.phone }}</li>
            <li><strong>Отделение:</strong> г. {{ orderForm.city }}, {{ orderForm.europostOffice }}</li>
            <li><strong>Сумма товаров:</strong> {{ formatPrice(productsTotal) }} BYN (+ доставка)</li>
          </ul>
          <p class="warning-passport-note">
            Для получения посылки на Европочте обязательно предъявление паспорта (или иного документа, удостоверяющего личность).
          </p>
          <div class="warning-actions">
            <button type="button" class="btn-warn-cancel" @click="isWarningModalOpen = false">Проверить данные</button>
            <button type="button" class="btn-warn-confirm" @click="confirmFinalOrder">Понятно, подтвердить</button>
          </div>
        </div>
      </div>
    </aside>
  </Transition>
</template>




<style scoped>
.cart-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(3px);
  z-index: 250;
}

.cart-drawer {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 480px;
  max-width: 100vw;
  background-color: #ffffff;
  color: #0f172a;
  z-index: 300;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 30px rgba(15, 23, 42, 0.25);
}

.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background-color: #0f172a;
  color: #ffffff;
}

.cart-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-back-step {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(163, 210, 249, 0.4);
  background: rgba(163, 210, 249, 0.12);
  color: #A3D2F9;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex; 
  align-items: center; 
  justify-content: center;
}

.btn-back-step:hover {
  background: #A3D2F9;
  color: #0f172a;
}

.cart-title {
  font-size: 18px;
  font-weight: 800;
}

.cart-count-pill {
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}

.cart-close {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
  display: inline-flex; 
  align-items: center; 
  justify-content: center;
}

.cart-close:hover {
  background-color: rgba(255, 255, 255, 0.12);
}

.price-mode-banner {
  padding: 9px 20px;
  background-color: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  color: #334155;
}

.price-mode-banner.wholesale {
  background-color: rgba(163, 210, 249, 0.35);
  color: #0f172a;
}

.cart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px;
  gap: 10px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 6px;
}

.cart-empty h3 {
  font-size: 18px;
  font-weight: 700;
}

.cart-empty p {
  font-size: 14px;
  color: #64748b;
  max-width: 280px;
}

.btn-back-catalog {
  margin-top: 10px;
  padding: 11px 20px;
  border-radius: 12px;
  border: none;
  background-color: #A3D2F9;
  color: #0f172a;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}

.cart-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.cart-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cart-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 14px;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
}

.item-thumb {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #A3D2F9 0%, #D4EAFC 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  flex-shrink: 0;
  overflow: hidden;
}

.item-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.item-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.item-sku {
  display: block;
  font-size: 11px;
  color: #64748b;
}

.item-name {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
}

.item-remove {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 15px;
  padding: 2px 4px;
}

.item-remove:hover {
  color: #ef4444;
}

.item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.qty-control {
  display: inline-flex;
  align-items: center;
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  overflow: hidden;
}

.qty-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
}

.qty-btn:hover {
  background-color: #A3D2F9;
}

.qty-value {
  min-width: 28px;
  text-align: center;
  font-size: 14px;
  font-weight: 700;
}

.item-price-block {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.item-old-price {
  font-size: 11px;
  color: #94a3b8;
  text-decoration: line-through;
}

.item-current-price {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
}

.item-unit-note {
  font-size: 11px;
  color: #64748b;
}

.checkout-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.checkout-scroll {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.wholesale-box {
  background-color: rgba(163, 210, 249, 0.22);
  border: 1px solid #A3D2F9;
  padding: 12px;
  border-radius: 12px;
}

.section-heading {
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-group label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.field-group input {
  height: 40px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  font-size: 13px;
  color: #0f172a;
  outline: none;
}

.field-group input:focus {
  border-color: #0284c7;
  box-shadow: 0 0 0 3px rgba(163, 210, 249, 0.4);
}

.field-note {
  font-size: 11px;
  color: #64748b;
  line-height: 1.3;
}

.radio-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background-color: #f8fafc;
  cursor: pointer;
  transition: all 0.15s ease;
}

.radio-card:hover {
  border-color: #A3D2F9;
}

.radio-card.selected {
  border-color: #0284c7;
  background-color: rgba(163, 210, 249, 0.25);
}

.hidden-radio {
  display: none;
}

.radio-info {
  display: flex;
  flex-direction: column;
}

.radio-title {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.radio-desc {
  font-size: 11px;
  color: #64748b;
}

.radio-check {
  font-size: 16px;
  font-weight: 700;
  color: #0284c7;
}

.europost-alert {
  display: flex;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  color: #78350f;
}

.alert-icon {
  font-size: 20px;
  line-height: 1.2;
}

.alert-text strong {
  display: block;
  font-size: 13px;
  margin-bottom: 2px;
}

.alert-text p {
  font-size: 12px;
  line-height: 1.4;
}

.checkout-error {
  background-color: #fee2e2;
  color: #b91c1c;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
}

.cart-footer {
  padding: 16px 20px 20px;
  border-top: 1px solid #e2e8f0;
  background-color: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-row.small {
  font-size: 13px;
  color: #475569;
}

.summary-row.savings {
  font-size: 13px;
  font-weight: 600;
  color: #0284c7;
}

.summary-row.total {
  font-size: 16px;
  font-weight: 700;
  margin-top: 2px;
}

.total-amount {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.btn-checkout {
  margin-top: 4px;
  height: 46px;
  width: 100%;
  border: none;
  border-radius: 12px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.btn-checkout:hover {
  background-color: #7cc0f8;
}

.btn-checkout:active {
  transform: scale(0.99);
}

/* Всплывающее предупредительное окно подтверждения */
.warning-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.78);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px;
  z-index: 350;
}

.warning-dialog {
  width: 100%;
  background-color: #ffffff;
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.warning-badge {
  align-self: flex-start;
  background-color: #fef3c7;
  color: #92400e;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 8px;
}

.warning-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.warning-body {
  font-size: 14px;
  color: #334155;
  line-height: 1.45;
}

.warning-checklist {
  list-style: none;
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #0f172a;
}

.warning-passport-note {
  font-size: 12px;
  color: #b45309;
  font-weight: 600;
  line-height: 1.35;
}

.warning-actions {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 8px;
  margin-top: 4px;
}

.btn-warn-cancel {
  height: 42px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background-color: #f8fafc;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-warn-confirm {
  height: 42px;
  border-radius: 10px;
  border: none;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.btn-warn-confirm:hover {
  background-color: #7cc0f8;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
}

.wholesale-delivery-notice {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  background-color: rgba(163, 210, 249, 0.28);
  border: 1.5px solid #0284c7;
  color: #0f172a;
}

.notice-icon {
  font-size: 22px;
  line-height: 1.2;
}

.notice-content strong {
  display: block;
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 3px;
  color: #0f172a;
}

.notice-content p {
  font-size: 12px;
  line-height: 1.45;
  color: #334155;
}

.wholesale-min-alert {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  font-size: 12px;
  color: #78350f;
}

.btn-fill-min {
  height: 28px;
  padding: 0 10px;
  border-radius: 8px;
  border: none;
  background-color: #0f172a;
  color: #A3D2F9;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.footer-min-warning {
  padding: 8px 10px;
  border-radius: 10px;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  font-size: 12px;
  font-weight: 600;
}

.btn-checkout:disabled {
  background-color: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.cart-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-clear-cart {
  height: 34px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid rgba(248, 113, 113, 0.45);
  background: rgba(239, 68, 68, 0.14);
  color: #fca5a5;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-clear-cart:hover {
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

.btn-export-smeta {
  height: 40px;
  width: 100%;
  border-radius: 12px;
  border: 1.5px solid #16a34a;
  background-color: #dcfce7;
  color: #15803d;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-export-smeta:hover {
  background-color: #16a34a;
  color: #ffffff;
}


</style>
