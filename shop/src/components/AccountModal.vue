<script setup>
import { ref, reactive, watch } from 'vue'
import * as XLSX from 'xlsx'
import { api } from '../services/api.js'
import {
  Building2,
  User,
  X,
  Clock,
  XCircle,
  ShoppingBag,
  ClipboardList,
  Package,
  Truck,
  Store,
  CheckCircle2,
  Handshake,
  FileSpreadsheet,
  RotateCw
} from 'lucide-vue-next'
import { useBackdropClose } from '../composables/useBackdropClose.js'


const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  currentUser: {
    type: Object,
    default: null
  },
  orders: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'logout', 'repeat-order', 'user-updated'])
const { onBackdropMouseDown, onBackdropMouseUp } = useBackdropClose(() => emit('close'))

const localUser = ref(props.currentUser ? { ...props.currentUser } : null)

watch(
  () => props.currentUser,
  (newVal) => {
    localUser.value = newVal ? { ...newVal } : null
  },
  { deep: true, immediate: true }
)

const isUpgradeFormOpen = ref(false)
const isSwitching = ref(false)
const switchError = ref('')

const upgradeForm = reactive({
  unp: '',
  companyName: ''
})

const openUpgradeForm = () => {
  switchError.value = ''
  upgradeForm.unp = localUser.value?.unp || ''
  upgradeForm.companyName = localUser.value?.companyName || (localUser.value?.role === 'wholesale' ? localUser.value.name : '')
  isUpgradeFormOpen.value = true
}

const onUnpInput = (event) => {
  const digitsOnly = event.target.value.replace(/[^0-9]/g, '').slice(0, 9)
  upgradeForm.unp = digitsOnly
  event.target.value = digitsOnly
}

const submitUpgradeToWholesale = async () => {
  switchError.value = ''
  if (upgradeForm.unp.length !== 9) {
    switchError.value = 'УНП должен состоять ровно из 9 цифр'
    return
  }
  if (!upgradeForm.companyName.trim()) {
    switchError.value = 'Укажите наименование организации или ИП'
    return
  }

  isSwitching.value = true
  try {
    const result = await api.switchRole({
      role: 'wholesale',
      unp: upgradeForm.unp,
      company_name: upgradeForm.companyName.trim()
    })

    const updatedUser = result?.user
      ? result.user
      : {
          ...localUser.value,
          wholesaleStatus: 'pending',
          unp: upgradeForm.unp,
          companyName: upgradeForm.companyName.trim()
        }

    localUser.value = { ...updatedUser }
    emit('user-updated', { ...result, user: updatedUser })
    isUpgradeFormOpen.value = false
  } catch (err) {
    switchError.value = err.message || 'Не удалось отправить заявку'
  } finally {
    isSwitching.value = false
  }
}

const switchToRetail = async () => {
  switchError.value = ''
  isSwitching.value = true
  try {
    const result = await api.switchRole({ role: 'retail' })

    const updatedUser = result?.user
      ? result.user
      : {
          ...localUser.value,
          role: 'retail',
          name: localUser.value?.contactName || localUser.value?.name
        }

    localUser.value = { ...updatedUser }
    emit('user-updated', { ...result, user: updatedUser })
    isUpgradeFormOpen.value = false
  } catch (err) {
    switchError.value = err.message || 'Не удалось переключить на физлицо'
  } finally {
    isSwitching.value = false
  }
}

const getStatusBadge = (status) => {
  const map = {
    processing: { label: 'В обработке', class: 'status-processing', icon: Clock },
    europost_pending: { label: 'Уточняется доставка Европочтой', class: 'status-europost', icon: Package },
    shipped: { label: 'Отправлено Европочтой', class: 'status-shipped', icon: Truck },
    ready_pickup: { label: 'Готово к самовывозу (ЭКСПОБЕЛ)', class: 'status-ready', icon: Store },
    completed: { label: 'Выполнено', class: 'status-completed', icon: CheckCircle2 }
  }
  return map[status] || map.processing
}


const formatPrice = (value) => {
  return Number(value).toFixed(2).replace('.', ',')
}

const handleLogoutClick = () => {
  isUpgradeFormOpen.value = false
  emit('logout')
  emit('close')
}

const exportOrderToExcel = (order) => {
  if (!localUser.value || localUser.value.role !== 'wholesale') return

  const sheetRows = [
    ['Заявка №', order.number, '', 'Дата:', order.createdAt],
    [],
    ['ПОСТАВЩИК:', 'ООО «Сандринтайм»', '', 'ПОКУПАТЕЛЬ:', localUser.value.name],
    ['УНП поставщика:', '690876665', '', 'УНП покупателя:', localUser.value.unp || '—'],
    ['Юридический адрес:', '223053, Минский р-н, Боровлянский с/с, д. Боровая, д. 7, ком. 1', '', 'Контактное лицо:', order.recipient?.full_name || localUser.value.contactName || '—'],
    ['Фактический адрес:', 'Минский р-н, пересечение Логойского тракта и МКАД, ТРЦ «Экспобел», пав. 218/219', '', 'Телефон покупателя:', order.recipient?.phone || '—'],
    ['Телефоны:', '+375 (29) 651-19-83, +375 (29) 000-00-00', '', '', ''],
    [],
    ['№', 'Артикул', 'Наименование товара', 'Кол-во (шт.)', 'Цена за шт. (BYN)', 'Сумма (BYN)']
  ]

  order.items.forEach((item, index) => {
    const qty = Number(item.quantity || 0)
    const price = Number(item.unit_price || 0)
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
  sheetRows.push(['', '', '', '', 'ИТОГО (BYN):', Number(order.products_total_byn || 0)])

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
  XLSX.utils.book_append_sheet(workbook, worksheet, `Заявка ${order.number}`)
  XLSX.writeFile(workbook, `Order_${order.number}_SandrinTime.xlsx`)
}
</script>




<template>
  <Transition name="modal-fade">
    <div
      v-if="isOpen"
      class="modal-backdrop"
      @mousedown.self="onBackdropMouseDown"
      @mouseup.self="onBackdropMouseUp"
    >

      <div class="account-card" role="dialog" aria-modal="true" aria-label="Личный кабинет">
        
                <div class="account-header">
          <div class="header-left">
            <span class="header-icon">{{ localUser?.role === 'wholesale' ? '🏢' : '👤' }}</span>
            <div>
              <h2 class="account-title">Личный кабинет</h2>
              <p class="account-subtitle">История заявок и отслеживание статусов</p>
            </div>
          </div>
          <button type="button" class="close-btn" @click="emit('close')" aria-label="Закрыть"><X :size="18" /></button>
        </div>

        <div v-if="localUser" class="profile-summary-wrapper">
          <div class="profile-summary">
            <div class="profile-details">
              <div class="profile-name-row">
                <strong class="profile-name">{{ localUser.name }}</strong>
                <span v-if="localUser.role === 'wholesale'" class="role-pill wholesale">
                  Опт • УНП {{ localUser.unp }}
                </span>
                <span v-else-if="localUser.wholesaleStatus === 'pending'" class="role-pill pending">
                  ⏳ Заявка на опт на проверке ({{ localUser.companyName }}, УНП {{ localUser.unp }})
                </span>
                <span v-else-if="localUser.wholesaleStatus === 'rejected'" class="role-pill rejected">
                  ❌ Заявка на опт отклонена
                </span>
                <span v-else class="role-pill">Розничный покупатель</span>
              </div>
              <span class="profile-email">{{ localUser.email }}</span>
            </div>

            <div class="profile-actions">
              <button 
                v-if="localUser.role === 'retail' && localUser.wholesaleStatus !== 'pending'" 
                type="button" 
                class="btn-switch-role wholesale"
                @click="openUpgradeForm"
              >
                🏢 {{ localUser.wholesaleStatus === 'rejected' ? 'Подать заявку повторно' : 'Перейти на юрлицо (опт)' }}
              </button>

              <button 
                v-else-if="localUser.role === 'wholesale'" 
                type="button" 
                class="btn-switch-role"
                :disabled="isSwitching"
                @click="switchToRetail"
              >
                🛍️ Вернуться на физлицо
              </button>

              <button type="button" class="btn-account-logout" @click="handleLogoutClick">
                Выйти
              </button>
            </div>
          </div>



          <form v-if="isUpgradeFormOpen" class="upgrade-form" @submit.prevent="submitUpgradeToWholesale">
            <div class="upgrade-header">
              <strong>Подключение оптового аккаунта (Юрлицо / ИП)</strong>
              <button type="button" class="btn-close-upgrade" @click="isUpgradeFormOpen = false">✕</button>
            </div>
            <div class="upgrade-fields">
              <div class="upgrade-field">
                <label>УНП (9 цифр) *</label>
                <div v-if="unpStatusMessage" class="unp-check-status" :class="{ verified: isUnpVerified }">
                  {{ unpStatusMessage }}
                </div>
            <div v-if="switchError" class="switch-error">{{ switchError }}</div>
            <button type="submit" class="btn-confirm-upgrade" :disabled="isSwitching">
              {{ isSwitching ? 'Отправка...' : 'Отправить заявку менеджеру' }}
            </button>


                <input 
                  :value="upgradeForm.unp" 
                  @input="onUnpInput" 
                  type="text" 
                  inputmode="numeric"
                  maxlength="9"
                  placeholder="690876665" 
                  required 
                />
              </div>
              <div class="upgrade-field">
                <label>Наименование организации / ИП *</label>
                <input 
                  v-model="upgradeForm.companyName" 
                  type="text" 
                  placeholder="ООО «Сандринтайм»" 
                  required 
                />
              </div>
            </div>
            <div v-if="switchError" class="switch-error">{{ switchError }}</div>
            <button type="submit" class="btn-confirm-upgrade" :disabled="isSwitching">
              {{ isSwitching ? 'Сохранение...' : 'Активировать оптовые цены' }}
            </button>
          </form>
        </div>

        <div class="orders-section">
          <div class="orders-top-row">
            <h3 class="orders-heading">Мои заявки ({{ orders.length }})</h3>
            <span class="orders-hint">Статус обновляется после проверки менеджером</span>
          </div>

          <div v-if="orders.length === 0" class="empty-orders">
            <div class="empty-icon"><ClipboardList :size="40" color="#94a3b8" /></div>
            <h4>У вас пока нет оформленных заявок</h4>
            <p>Добавьте интересующие модели часов в корзину и оформите заявку — она сразу появится здесь.</p>
            <button type="button" class="btn-go-shop" @click="emit('close')">
              Перейти в каталог
            </button>
          </div>

          <div v-else class="orders-list">
            <article v-for="order in orders" :key="order.id" class="order-item">
              <div class="order-head">
                <div class="order-id-block">
                  <span class="order-number">Заявка №{{ order.number }}</span>
                  <span class="order-date">от {{ order.createdAt }}</span>
                </div>
                  <span class="status-badge" :class="getStatusBadge(order.status).class" style="display: inline-flex; align-items: center; gap: 5px;">
                    <component :is="getStatusBadge(order.status).icon" :size="13" />
                    <span>{{ getStatusBadge(order.status).label }}</span>
                  </span>

              </div>

            <div class="order-delivery-info">
              <template v-if="order.delivery.method === 'manager'">
                <div class="delivery-line">
                  <strong><Handshake :size="14" /> Доставка и оплата:</strong> Согласование с менеджером (оптовый заказ)
                </div>
                <div class="delivery-line">
                  <strong>Контактное лицо:</strong> {{ order.recipient.full_name }} ({{ order.recipient.phone }})
                </div>
              </template>


                <template v-else-if="order.delivery.method === 'europost'">
                  <div class="delivery-line">
                    <strong><Package :size="14" /> Европочта:</strong> г. {{ order.delivery.city }}, {{ order.delivery.office }}
                  </div>
                  <div class="delivery-line">
                    <strong>Получатель:</strong> {{ order.recipient.full_name }} ({{ order.recipient.phone }})
                  </div>
                  <div v-if="order.delivery.track_code" class="delivery-line track-box">
                    <strong>Трек-номер для отслеживания:</strong> {{ order.delivery.track_code }}
                  </div>
                </template>

                <template v-else>
                  <div class="delivery-line">
                    <strong><Store :size="14" /> Самовывоз:</strong> Рынок «ЭКСПОБЕЛ», пав. 218/219, 1 этаж, 4 ряд
                  </div>
                  <div class="delivery-line">
                    <strong>Получатель:</strong> {{ order.recipient.full_name }} ({{ order.recipient.phone }})
                  </div>
                </template>
              </div>


              <ul class="order-products">
                <li v-for="item in order.items" :key="item.product_id" class="order-product-row">
                  <span class="prod-name">
                    <span class="prod-sku">[{{ item.sku }}]</span> {{ item.name }}
                  </span>
                  <span class="prod-qty-price">
                    {{ item.quantity }} шт. × {{ formatPrice(item.unit_price) }} BYN
                  </span>
                </li>
              </ul>

              <div class="order-foot">
                <div class="order-total">
                  Сумма товаров: <strong>{{ formatPrice(order.products_total_byn) }} BYN</strong>
                  <span v-if="order.delivery.method === 'europost'" class="delivery-note">
                    (+ доставка Европочтой)
                  </span>
                </div>

                <div class="order-foot-actions">
                  <button
                    v-if="localUser?.role === 'wholesale'"
                    type="button"
                    class="btn-excel-order"
                    @click="exportOrderToExcel(order)"
                    title="Выгрузить состав заявки в файл Excel (.xlsx)"
                  >
                    <FileSpreadsheet :size="14" /> В Excel
                  </button>

                  <button 
                    type="button" 
                    class="btn-repeat" 
                    @click="emit('repeat-order', order.items); emit('close')"
                  >
                    <RotateCw :size="13" /> Повторить заявку
                  </button>
                </div>

              </div>

            </article>
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
  z-index: 320;
  overflow-y: auto;
}

.account-card {
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  background-color: #ffffff;
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #0f172a;
}

/* Шапка окна */
.account-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  background-color: #0f172a;
  color: #ffffff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background-color: rgba(163, 210, 249, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.account-title {
  font-size: 19px;
  font-weight: 800;
}

.account-subtitle {
  font-size: 12px;
  color: #94a3b8;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.12);
}

/* Блок профиля */
.profile-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 24px;
  background-color: rgba(163, 210, 249, 0.25);
  border-bottom: 1px solid #A3D2F9;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.profile-name {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.role-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 999px;
  background-color: #ffffff;
  color: #334155;
}

.role-pill.wholesale {
  background-color: #0f172a;
  color: #A3D2F9;
}

.profile-email {
  font-size: 13px;
  color: #475569;
}

.btn-account-logout {
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #b91c1c;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-account-logout:hover {
  background-color: #fee2e2;
  border-color: #fca5a5;
}

/* Раздел заявок */
.orders-section {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.orders-top-row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.orders-heading {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.orders-hint {
  font-size: 12px;
  color: #64748b;
}

/* Пустой список заявок */
.empty-orders {
  text-align: center;
  padding: 36px 16px;
  background-color: #f8fafc;
  border-radius: 16px;
  border: 1px dashed #cbd5e1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-icon {
  font-size: 40px;
}

.empty-orders h4 {
  font-size: 16px;
  font-weight: 700;
}

.empty-orders p {
  font-size: 13px;
  color: #64748b;
  max-width: 340px;
}

.btn-go-shop {
  margin-top: 6px;
  padding: 10px 18px;
  border-radius: 10px;
  border: none;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

/* Карточки заявок */
.orders-list {
display: flex;
flex-direction: column;
gap: 14px;
}
.order-item {
border: 1px solid #e2e8f0;
border-radius: 16px;
background-color: #f8fafc;
padding: 16px;
display: flex;
flex-direction: column;
gap: 12px;
}
.order-head {
display: flex;
flex-wrap: wrap;
align-items: center;
justify-content: space-between;
gap: 8px;
padding-bottom: 10px;
border-bottom: 1px solid #e2e8f0;
}
.order-id-block {
display: flex;
align-items: baseline;
gap: 8px;
}
.order-number {
font-size: 15px;
font-weight: 800;
color: #0f172a;
}
.order-date {
font-size: 12px;
color: #64748b;
}
/* Бейджи статусов */
.status-badge {
font-size: 12px;
font-weight: 700;
padding: 4px 10px;
border-radius: 999px;
}
.status-processing {
background-color: #e0f2fe;
color: #0369a1;
}
.status-europost {
background-color: #fef3c7;
color: #92400e;
}
.status-shipped {
background-color: #ede9fe;
color: #5b21b6;
}
.status-ready {
background-color: #dcfce7;
color: #166534;
}
.status-completed {
background-color: #f1f5f9;
color: #475569;
}
/* Блок доставки */
.order-delivery-info {
background-color: #ffffff;
border: 1px solid #e2e8f0;
border-radius: 10px;
padding: 10px 12px;
display: flex;
flex-direction: column;
gap: 4px;
font-size: 13px;
color: #334155;
}
.track-box {
margin-top: 4px;
padding-top: 4px;
border-top: 1px dashed #cbd5e1;
color: #0284c7;
}
/* Товары в заявке */
.order-products {
list-style: none;
display: flex;
flex-direction: column;
gap: 6px;
}
.order-product-row {
display: flex;
justify-content: space-between;
align-items: baseline;
gap: 12px;
font-size: 13px;
}
.prod-sku {
color: #64748b;
font-size: 12px;
}
.prod-qty-price {
font-weight: 600;
color: #0f172a;
white-space: nowrap;
}
/* Подвал заявки */
.order-foot {
display: flex;
flex-wrap: wrap;
align-items: center;
justify-content: space-between;
gap: 10px;
padding-top: 10px;
border-top: 1px solid #e2e8f0;
}
.order-total {
font-size: 14px;
color: #0f172a;
}
.order-total strong {
font-size: 16px;
font-weight: 800;
}
.delivery-note {
font-size: 12px;
color: #64748b;
}
.btn-repeat {
height: 34px;
padding: 0 12px;
border-radius: 9px;
border: 1px solid #cbd5e1;
background-color: #ffffff;
color: #0f172a;
font-size: 12px;
font-weight: 700;
cursor: pointer;
transition: all 0.15s ease;
}
.btn-repeat:hover {
background-color: #A3D2F9;
border-color: #A3D2F9;
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
@media (max-width: 600px) {
.account-header,
.profile-summary,
.orders-section {
padding-left: 16px;
padding-right: 16px;
}
.order-product-row {
flex-direction: column;
gap: 2px;
}
}

.profile-summary-wrapper {
  background-color: rgba(163, 210, 249, 0.25);
  border-bottom: 1px solid #A3D2F9;
}

.profile-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 24px;
}

.profile-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-switch-role {
  height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1px solid #0284c7;
  background-color: #ffffff;
  color: #0284c7;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-switch-role.wholesale {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
}

.btn-switch-role:hover:not(:disabled) {
  opacity: 0.9;
}

.upgrade-form {
  margin: 0 24px 16px;
  padding: 14px;
  background-color: #ffffff;
  border: 1.5px solid #0284c7;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upgrade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #0f172a;
}

.btn-close-upgrade {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
}

.upgrade-fields {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 10px;
}

.upgrade-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upgrade-field label {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.upgrade-field input {
  height: 38px;
  padding: 0 10px;
  border-radius: 9px;
  border: 1.5px solid #cbd5e1;
  font-size: 13px;
  color: #0f172a;
  outline: none;
}

.upgrade-field input:focus {
  border-color: #0284c7;
}

.switch-error {
  font-size: 12px;
  font-weight: 600;
  color: #b91c1c;
}

.btn-confirm-upgrade {
  height: 38px;
  border: none;
  border-radius: 10px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.btn-confirm-upgrade:hover:not(:disabled) {
  background-color: #7cc0f8;
}

@media (max-width: 600px) {
  .upgrade-fields {
    grid-template-columns: 1fr;
  }
}

.order-foot-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-invoice {
  height: 34px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1px solid #0284c7;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-invoice:hover {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-excel-order {
  height: 34px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1px solid #16a34a;
  background-color: #dcfce7;
  color: #15803d;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-excel-order:hover {
  background-color: #16a34a;
  color: #ffffff;
}

.role-pill.pending {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #f59e0b;
}

.role-pill.rejected {
  background-color: #fee2e2;
  color: #b91c1c;
}


</style>