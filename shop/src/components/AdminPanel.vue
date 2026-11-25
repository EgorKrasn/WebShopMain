<script setup>
import { ref, computed, onMounted, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../services/api.js'
import {
  Settings,
  RefreshCw,
  ArrowUpRight,
  ArrowLeft,
  Building2,
  Package,
  Watch,
  FolderTree,
  Archive,
  Rocket,
  FileArchive
} from 'lucide-vue-next'

import AdminWholesaleTab from './admin/AdminWholesaleTab.vue'
import AdminOrdersTab from './admin/AdminOrdersTab.vue'
import AdminArchiveTab from './admin/AdminArchiveTab.vue'
import AdminProductsTab from './admin/AdminProductsTab.vue'
import AdminCategoriesTab from './admin/AdminCategoriesTab.vue'
import AdminBackupTab from './admin/AdminBackupTab.vue'

const emit = defineEmits(['close', 'categories-updated', 'products-updated', 'catalog-restored'])

const route = useRoute()
const router = useRouter()

const activeTab = computed({
  get() {
    return route.params.section ? String(route.params.section) : 'menu'
  },
  set(newSection) {
    if (!newSection || newSection === 'menu') {
      router.push({ name: 'admin' })
    } else {
      router.push({ name: 'admin', params: { section: newSection } })
    }
  }
})

const isLoading = ref(false)
const actionMessage = ref('')
const errorMessage = ref('')

const wholesaleRequests = ref([])
const allOrders = ref([])
const archiveOrders = ref([])
const allProducts = ref([])
const allCategories = ref([])

const orderDrafts = ref({})
const productQuickDrafts = ref({})

const ordersTotalCount = ref(0)
const hasMoreOrders = ref(false)
const isLoadingMoreOrders = ref(false)

const archiveTotalCount = ref(0)
const hasMoreArchive = ref(false)
const isLoadingMoreArchive = ref(false)

const ORDERS_PAGE_SIZE = 20

const showToast = (msg) => {
  actionMessage.value = msg
  setTimeout(() => {
    actionMessage.value = ''
  }, 3000)
}

const setError = (msg) => {
  errorMessage.value = msg
}

const pendingWholesaleCount = computed(() => {
  return wholesaleRequests.value.filter((u) => u.wholesaleStatus === 'pending').length
})

const outOfStockCount = computed(() => {
  return allProducts.value.filter((p) => (p.stock ?? 0) <= 0).length
})

const adminSections = computed(() => [
  {
    id: 'wholesale',
    group: 'Продажи и клиенты',
    icon: markRaw(Building2),
    accent: 'gold',
    title: 'Заявки юрлиц (УНП)',
    description: 'Проверка реквизитов компаний и ИП, одобрение и отключение оптового доступа.',
    badge: pendingWholesaleCount.value > 0 ? `${pendingWholesaleCount.value} новых` : '',
    badgeType: 'urgent',
    meta: `Всего заявок: ${wholesaleRequests.value.length}`
  },
  {
    id: 'orders',
    group: 'Продажи и клиенты',
    icon: markRaw(Package),
    accent: 'blue',
    title: 'Управление заказами',
    description: 'Обработка розничных и оптовых заказов, смена статусов, трек-коды Европочты и архив.',
    badge: allOrders.value.length > 0 ? `${allOrders.value.length} в работе` : '',
    badgeType: 'info',
    meta: `Всего в выборке: ${ordersTotalCount.value || allOrders.value.length}`
  },
  {
    id: 'products',
    group: 'Каталог и склад',
    icon: markRaw(Watch),
    accent: 'emerald',
    title: 'Товары и остатки',
    description: 'Добавление моделей, загрузка фото, быстрое редактирование розничных/оптовых цен и остатков.',
    badge: outOfStockCount.value > 0 ? `Нет на складе: ${outOfStockCount.value}` : '',
    badgeType: 'warn',
    meta: `Позиций в базе: ${allProducts.value.length}`
  },
  {
    id: 'categories',
    group: 'Каталог и склад',
    icon: markRaw(FolderTree),
    accent: 'purple',
    title: 'Категории и подкатегории',
    description: 'Настройка структуры меню каталога, иконок разделов, порядка сортировки и подразделов.',
    badge: '',
    badgeType: 'neutral',
    meta: `Разделов: ${allCategories.value.length}`
  },
  {
    id: 'archive',
    group: 'Продажи и клиенты',
    icon: markRaw(Archive),
    accent: 'slate',
    title: 'Архив выполненных заявок',
    description: 'История завершённых и отменённых заказов с возможностью просмотра и восстановления.',
    badge: '',
    badgeType: 'neutral',
    meta: `В архиве: ${archiveTotalCount.value}`
  },
  {
    id: 'backup',
    group: 'Система и данные',
    icon: markRaw(FileArchive),
    accent: 'indigo',
    title: 'Резервное копирование',
    description: 'Экспорт всего каталога, категорий и фотографий в единый .zip-архив и восстановление.',
    badge: '',
    badgeType: 'neutral',
    meta: 'Формат: .ZIP (БД + uploads)'
  }
])
const activeSectionTitle = computed(() => {
  const found = adminSections.value.find((s) => s.id === activeTab.value)
  return found ? found.title : ''
})

const fillOrderDrafts = (ordersArray) => {
  const updated = { ...orderDrafts.value }
  for (const o of ordersArray) {
    updated[o.id] = { status: o.status, trackCode: o.trackCode || '' }
  }
  orderDrafts.value = updated
}

const syncProductsState = (productsList) => {
  allProducts.value = Array.isArray(productsList) ? productsList : []
  const pDrafts = {}
  for (const p of allProducts.value) {
    pDrafts[p.id] = {
      retailPrice: p.retailPrice,
      wholesalePrice: p.wholesalePrice,
      stock: p.stock ?? 0
    }
  }
  productQuickDrafts.value = pDrafts
}

const loadAdminData = async () => {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [reqRes, ordersRes, productsRes, categoriesRes, archiveRes] = await Promise.allSettled([
      api.adminGetWholesaleRequests(),
      api.adminGetOrders('active', ORDERS_PAGE_SIZE, 0),
      api.getProducts(),
      api.getCategories(),
      api.adminGetOrders('archive', ORDERS_PAGE_SIZE, 0)
    ])

    if (reqRes.status === 'fulfilled') {
      wholesaleRequests.value = Array.isArray(reqRes.value) ? reqRes.value : []
    }

    orderDrafts.value = {}

    if (ordersRes.status === 'fulfilled') {
      const data = ordersRes.value
      const items = Array.isArray(data) ? data : (Array.isArray(data?.items) ? data.items : [])
      allOrders.value = items
      ordersTotalCount.value = Array.isArray(data) ? items.length : (data?.total ?? items.length)
      hasMoreOrders.value = Boolean(data?.hasMore)
      fillOrderDrafts(allOrders.value)
    }

    if (archiveRes.status === 'fulfilled') {
      const aData = archiveRes.value
      const aItems = Array.isArray(aData) ? aData : (Array.isArray(aData?.items) ? aData.items : [])
      archiveOrders.value = aItems
      archiveTotalCount.value = Array.isArray(aData) ? aItems.length : (aData?.total ?? aItems.length)
      hasMoreArchive.value = Boolean(aData?.hasMore)
      fillOrderDrafts(archiveOrders.value)
    }

    if (productsRes.status === 'fulfilled') {
      syncProductsState(productsRes.value)
    }

    if (categoriesRes.status === 'fulfilled') {
      allCategories.value = Array.isArray(categoriesRes.value) ? categoriesRes.value : []
    }

    const firstRejected = [reqRes, ordersRes, productsRes, categoriesRes, archiveRes].find(
      (r) => r.status === 'rejected'
    )
    if (firstRejected) {
      errorMessage.value = firstRejected.reason?.message || 'Часть данных не загрузилась'
    }
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadAdminData()
})

const handleWholesaleDecision = async ({ userId, decision }) => {
  errorMessage.value = ''
  try {
    await api.adminReviewWholesale(userId, decision)
    const target = wholesaleRequests.value.find((u) => u.id === userId)
    if (target) {
      target.wholesaleStatus = decision
      target.role = decision === 'approved' ? 'wholesale' : 'retail'
    }
    showToast(decision === 'approved' ? 'Оптовый доступ одобрен!' : 'Заявка отклонена')
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось обновить статус юрлица'
  }
}

const fetchOrdersList = async (reset = true) => {
  const offset = reset ? 0 : allOrders.value.length
  if (!reset) isLoadingMoreOrders.value = true
  try {
    const res = await api.adminGetOrders('active', ORDERS_PAGE_SIZE, offset)
    const loadedItems = Array.isArray(res?.items) ? res.items : []
    allOrders.value = reset ? loadedItems : [...allOrders.value, ...loadedItems]
    ordersTotalCount.value = res?.total ?? allOrders.value.length
    hasMoreOrders.value = Boolean(res?.hasMore)
    fillOrderDrafts(loadedItems)
  } finally {
    isLoadingMoreOrders.value = false
  }
}

const fetchArchiveList = async (reset = true) => {
  const offset = reset ? 0 : archiveOrders.value.length
  if (!reset) isLoadingMoreArchive.value = true
  try {
    const res = await api.adminGetOrders('archive', ORDERS_PAGE_SIZE, offset)
    const loadedItems = Array.isArray(res?.items) ? res.items : []
    archiveOrders.value = reset ? loadedItems : [...archiveOrders.value, ...loadedItems]
    archiveTotalCount.value = res?.total ?? archiveOrders.value.length
    hasMoreArchive.value = Boolean(res?.hasMore)
    fillOrderDrafts(loadedItems)
  } finally {
    isLoadingMoreArchive.value = false
  }
}

const saveOrderChanges = async (orderId) => {
  const draft = orderDrafts.value[orderId]
  if (!draft) return
  errorMessage.value = ''
  try {
    await api.adminUpdateOrder(orderId, {
      status: draft.status,
      trackCode: draft.trackCode
    })

    const isArchivedStatus = draft.status === 'completed' || draft.status === 'cancelled'
    const activeIdx = allOrders.value.findIndex((o) => o.id === orderId)
    const archiveIdx = archiveOrders.value.findIndex((o) => o.id === orderId)

    if (activeIdx !== -1) {
      const updatedOrder = {
        ...allOrders.value[activeIdx],
        status: draft.status,
        trackCode: draft.trackCode
      }
      if (isArchivedStatus) {
        allOrders.value.splice(activeIdx, 1)
        ordersTotalCount.value = Math.max(0, ordersTotalCount.value - 1)
        archiveOrders.value.unshift(updatedOrder)
        archiveTotalCount.value += 1
      } else {
        allOrders.value[activeIdx] = updatedOrder
      }
    } else if (archiveIdx !== -1) {
      const updatedOrder = {
        ...archiveOrders.value[archiveIdx],
        status: draft.status,
        trackCode: draft.trackCode
      }
      if (!isArchivedStatus) {
        archiveOrders.value.splice(archiveIdx, 1)
        archiveTotalCount.value = Math.max(0, archiveTotalCount.value - 1)
        allOrders.value.unshift(updatedOrder)
        ordersTotalCount.value += 1
      } else {
        archiveOrders.value[archiveIdx] = updatedOrder
      }
    }

    if (draft.status === 'cancelled' || archiveIdx !== -1) {
      const freshProducts = await api.getProducts()
      if (Array.isArray(freshProducts)) {
        syncProductsState(freshProducts)
        emit('products-updated')
      }
    }

    showToast(
      draft.status === 'cancelled'
        ? 'Заказ отменён, остатки возвращены на склад'
        : isArchivedStatus
          ? 'Заказ перенесён в архив'
          : 'Статус заказа обновлён'
    )
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка сохранения заказа'
  }
}

const handleDeleteOrder = async ({ order, fromArchive }) => {
  const warningText = fromArchive
    ? `Удалить архивный заказ №${order.number} из истории навсегда?`
    : `Удалить активный заказ №${order.number}? Товары из заказа автоматически вернутся на склад.`
  if (!confirm(warningText)) return

  errorMessage.value = ''
  try {
    await api.adminDeleteOrder(order.id)
    if (fromArchive) {
      archiveOrders.value = archiveOrders.value.filter((o) => o.id !== order.id)
      archiveTotalCount.value = Math.max(0, archiveTotalCount.value - 1)
    } else {
      allOrders.value = allOrders.value.filter((o) => o.id !== order.id)
      ordersTotalCount.value = Math.max(0, ordersTotalCount.value - 1)
      const freshProducts = await api.getProducts()
      if (Array.isArray(freshProducts)) {
        syncProductsState(freshProducts)
        emit('products-updated')
      }
    }
    showToast(fromArchive ? 'Запись удалена из архива' : 'Заказ удалён, остатки возвращены на склад')
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось удалить заказ'
  }
}

const handleProductsUpdated = async () => {
  try {
    const freshProducts = await api.getProducts()
    syncProductsState(freshProducts)
    emit('products-updated')
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось обновить список товаров'
  }
}

const handleCategoriesUpdated = async () => {
  try {
    const freshCategories = await api.getCategories()
    allCategories.value = Array.isArray(freshCategories) ? freshCategories : []
    emit('categories-updated')
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось обновить категории'
  }
}

const handleCatalogRestored = async () => {
  await loadAdminData()
  emit('categories-updated')
  emit('catalog-restored')
}
</script>

<template>
  <section class="admin-container">
    <div class="admin-top-bar">
      <div>
        <div v-if="activeTab !== 'menu'" class="admin-breadcrumbs">
          <button type="button" class="crumb-link" @click="activeTab = 'menu'">
            Главное меню
          </button>
          <span class="crumb-sep">/</span>
          <span class="crumb-current">{{ activeSectionTitle }}</span>
        </div>
        <h1 class="admin-title" style="display: flex; align-items: center; gap: 10px;">
          <Settings v-if="activeTab === 'menu'" :size="24" color="#A3D2F9" />
          <span>{{ activeTab === 'menu' ? 'Центр управления «СандринТайм»' : activeSectionTitle }}</span>
        </h1>
        <p class="admin-subtitle">
          {{
            activeTab === 'menu'
              ? 'Выберите нужный раздел для работы с магазином, клиентами и складом'
              : 'Управление выбранным разделом панели администратора'
          }}
        </p>
      </div>

      <div class="admin-top-actions">
        <button
          v-if="activeTab !== 'menu'"
          type="button"
          class="btn-back-menu"
          @click="activeTab = 'menu'"
        >
          <ArrowLeft :size="15" />
          <span>В меню админки</span>
        </button>
        <button type="button" class="btn-refresh" :disabled="isLoading" @click="loadAdminData">
          <RefreshCw :size="15" />
          <span>Обновить</span>
        </button>
        <button type="button" class="btn-back-store" @click="emit('close')">
          <span>В магазин</span>
          <ArrowUpRight :size="15" />
        </button>
      </div>
    </div>

    <div v-if="actionMessage" class="admin-toast">{{ actionMessage }}</div>
    <div v-if="errorMessage" class="admin-error">{{ errorMessage }}</div>

    <div v-if="isLoading" class="admin-loading">Загрузка данных...</div>

    <div v-else-if="activeTab === 'menu'" class="admin-hub">
      <div class="hub-kpi-row">
        <div class="kpi-card" @click="activeTab = 'wholesale'">
          <span class="kpi-label">Ожидают проверки УНП</span>
          <strong class="kpi-val" :class="{ alert: pendingWholesaleCount > 0 }">
            {{ pendingWholesaleCount }}
          </strong>
        </div>

        <div class="kpi-card" @click="activeTab = 'orders'">
          <span class="kpi-label">Активных заказов</span>
          <strong class="kpi-val">{{ allOrders.length }}</strong>
        </div>

        <div class="kpi-card" @click="activeTab = 'products'">
          <span class="kpi-label">Товаров в каталоге</span>
          <strong class="kpi-val">{{ allProducts.length }}</strong>
        </div>

        <div class="kpi-card" @click="activeTab = 'products'">
          <span class="kpi-label">Закончились на складе</span>
          <strong class="kpi-val" :class="{ warn: outOfStockCount > 0 }">
            {{ outOfStockCount }}
          </strong>
        </div>
      </div>

      <div class="hub-sections-grid">
        <button
          v-for="sec in adminSections"
          :key="sec.id"
          type="button"
          class="hub-module-card"
          @click="activeTab = sec.id"
        >
          <div class="hub-card-top">
            <div class="hub-icon-box" :class="sec.accent">
              <component :is="sec.icon" :size="24" :stroke-width="2.1" />
            </div>
            <span v-if="sec.badge" class="hub-badge" :class="sec.badgeType">
              {{ sec.badge }}
            </span>
          </div>

          <div class="hub-card-group">{{ sec.group }}</div>
          <h2 class="hub-card-title">{{ sec.title }}</h2>
          <p class="hub-card-desc">{{ sec.description }}</p>

          <div class="hub-card-foot">
            <span class="hub-meta">{{ sec.meta }}</span>
            <span class="hub-open-link">Открыть раздел →</span>
          </div>
        </button>

        <div class="hub-future-card">
          <div class="future-icon"><Rocket :size="28" color="#475569" /></div>
          <h3>Новые модули в разработке</h3>
          <p>
            Сюда легко подключатся аналитика продаж, промокоды, выгрузка отчётов,
            управление пользователями и интеграция со складом.
          </p>
        </div>
      </div>
    </div>

    <AdminWholesaleTab
      v-else-if="activeTab === 'wholesale'"
      :requests="wholesaleRequests"
      @decision="handleWholesaleDecision"
    />

    <AdminOrdersTab
      v-else-if="activeTab === 'orders'"
      :orders="allOrders"
      :order-drafts="orderDrafts"
      :has-more="hasMoreOrders"
      :is-loading-more="isLoadingMoreOrders"
      @save-order="saveOrderChanges"
      @delete-order="handleDeleteOrder"
      @load-more="fetchOrdersList(false)"
    />

    <AdminArchiveTab
      v-else-if="activeTab === 'archive'"
      :orders="archiveOrders"
      :order-drafts="orderDrafts"
      :has-more="hasMoreArchive"
      :is-loading-more="isLoadingMoreArchive"
      @save-order="saveOrderChanges"
      @delete-order="handleDeleteOrder"
      @load-more="fetchArchiveList(false)"
    />

    <AdminProductsTab
      v-else-if="activeTab === 'products'"
      :products="allProducts"
      :categories="allCategories"
      :quick-drafts="productQuickDrafts"
      @updated="handleProductsUpdated"
      @toast="showToast"
      @error="setError"
    />

    <AdminCategoriesTab
      v-else-if="activeTab === 'categories'"
      :categories="allCategories"
      @updated="handleCategoriesUpdated"
      @toast="showToast"
      @error="setError"
    />

    <AdminBackupTab
      v-else-if="activeTab === 'backup'"
      :categories-count="allCategories.length"
      :products-count="allProducts.length"
      @restored="handleCatalogRestored"
      @toast="showToast"
      @error="setError"
    />
  </section>
</template>

<style scoped>
.admin-container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  color: #0f172a;
}

.admin-top-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 18px 22px;
  background-color: #0f172a;
  color: #ffffff;
  border-radius: 18px;
}

.admin-title {
  font-size: 22px;
  font-weight: 800;
}

.admin-subtitle {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

.admin-top-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-refresh,
.btn-back-store {
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-refresh {
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.btn-back-store {
  border: none;
  background-color: #A3D2F9;
  color: #0f172a;
}

.admin-toast {
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #dcfce7;
  border: 1px solid #22c55e;
  color: #166534;
  font-weight: 700;
  margin-bottom: 16px;
}

.admin-error {
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  font-weight: 700;
  margin-bottom: 16px;
}

.admin-loading {
  padding: 40px;
  text-align: center;
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 15px;
}

.admin-breadcrumbs {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-bottom: 6px;
}

.crumb-link {
  background: transparent;
  border: none;
  padding: 0;
  color: #A3D2F9;
  font-weight: 700;
  cursor: pointer;
}

.crumb-link:hover {
  text-decoration: underline;
}

.crumb-sep {
  color: #64748b;
}

.crumb-current {
  color: #cbd5e1;
}

.btn-back-menu {
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #A3D2F9;
  background-color: rgba(163, 210, 249, 0.15);
  color: #A3D2F9;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-back-menu:hover {
  background-color: #A3D2F9;
  color: #0f172a;
}

.admin-hub {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.hub-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.kpi-card {
  background-color: rgba(255, 255, 255, 0.9);
  border: 1.5px solid #ffffff;
  border-radius: 16px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
}

.kpi-label {
  font-size: 12.5px;
  font-weight: 700;
  color: #64748b;
}

.kpi-val {
  font-size: 28px;
  font-weight: 900;
  color: #0f172a;
  line-height: 1.1;
}

.kpi-val.alert {
  color: #dc2626;
}

.kpi-val.warn {
  color: #d97706;
}

.hub-sections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}

.hub-module-card {
  text-align: left;
  background-color: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 20px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
  transition: all 0.2s ease;
}

.hub-module-card:hover {
  border-color: #0f172a;
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.14);
}

.hub-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.hub-icon-box {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hub-icon-box.gold {
  background-color: #fef3c7;
  color: #d97706;
}

.hub-icon-box.blue {
  background-color: #e0f2fe;
  color: #0284c7;
}

.hub-icon-box.emerald {
  background-color: #dcfce7;
  color: #16a34a;
}

.hub-icon-box.purple {
  background-color: #f3e8ff;
  color: #7c3aed;
}

.hub-icon-box.slate {
  background-color: #f1f5f9;
  color: #334155;
}

.hub-icon-box.indigo {
  background-color: #e0e7ff;
  color: #4338ca;
}

.hub-badge {
  font-size: 11.5px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 999px;
}

.hub-badge.urgent {
  background-color: #fee2e2;
  color: #b91c1c;
}

.hub-badge.info {
  background-color: #e0f2fe;
  color: #0369a1;
}

.hub-badge.warn {
  background-color: #fef3c7;
  color: #92400e;
}

.hub-card-group {
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #0284c7;
}

.hub-card-title {
  font-size: 19px;
  font-weight: 800;
  color: #0f172a;
}

.hub-card-desc {
  font-size: 13.5px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 8px;
}

.hub-card-foot {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hub-meta {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.hub-open-link {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.hub-module-card:hover .hub-open-link {
  color: #0284c7;
}

.hub-future-card {
  background-color: rgba(255, 255, 255, 0.55);
  border: 2px dashed #94a3b8;
  border-radius: 20px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  color: #475569;
}

.hub-future-card h3 {
  font-size: 16px;
  font-weight: 800;
  color: #334155;
}

.hub-future-card p {
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .hub-kpi-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 540px) {
  .hub-kpi-row {
    grid-template-columns: 1fr;
  }
}
</style>
