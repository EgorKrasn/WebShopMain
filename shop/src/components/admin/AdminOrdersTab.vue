<script setup>
import { ref, computed } from 'vue'
import {
  LayoutGrid,
  Clock,
  Package,
  Truck,
  Store,
  Building2,
  ShoppingBag,
  Trash2,
  X
} from 'lucide-vue-next'
import './admin.css'

const props = defineProps({
  orders: {
    type: Array,
    default: () => []
  },
  orderDrafts: {
    type: Object,
    default: () => ({})
  },
  hasMore: {
    type: Boolean,
    default: false
  },
  isLoadingMore: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['save-order', 'delete-order', 'load-more'])

const selectedOrderStatus = ref('all')
const selectedOrderRole = ref('all')
const orderSearchQuery = ref('')

const orderStatusFilters = [
  { value: 'all', label: 'Все активные', icon: LayoutGrid },
  { value: 'processing', label: 'В обработке', icon: Clock },
  { value: 'europost_pending', label: 'Уточняется Европочта', icon: Package },
  { value: 'shipped', label: 'Отправлено', icon: Truck },
  { value: 'ready_pickup', label: 'Готово к самовывозу', icon: Store }
]

const baseFilteredOrders = computed(() => {
  const q = orderSearchQuery.value.trim().toLowerCase()

  return props.orders.filter((order) => {
    const matchesRole =
      selectedOrderRole.value === 'all' || order.role === selectedOrderRole.value

    if (!matchesRole) return false
    if (!q) return true

    const numberMatch = (order.number || '').toLowerCase().includes(q)
    const nameMatch = (order.recipient?.full_name || '').toLowerCase().includes(q)
    const phoneMatch = (order.recipient?.phone || '').toLowerCase().includes(q)
    const companyMatch = (order.companyName || '').toLowerCase().includes(q)
    const unpMatch = (order.unp || '').toLowerCase().includes(q)

    return numberMatch || nameMatch || phoneMatch || companyMatch || unpMatch
  })
})

const orderCountsByStatus = computed(() => {
  const counts = { all: baseFilteredOrders.value.length }
  for (const order of baseFilteredOrders.value) {
    counts[order.status] = (counts[order.status] || 0) + 1
  }
  return counts
})

const filteredAdminOrders = computed(() => {
  if (selectedOrderStatus.value === 'all') {
    return baseFilteredOrders.value
  }
  return baseFilteredOrders.value.filter((o) => o.status === selectedOrderStatus.value)
})

const resetOrderFilters = () => {
  orderSearchQuery.value = ''
  selectedOrderRole.value = 'all'
  selectedOrderStatus.value = 'all'
}

const formatPrice = (value) => {
  return Number(value || 0).toFixed(2).replace('.', ',')
}
</script>

<template>
  <div class="tab-content">
    <div v-if="orders.length === 0" class="empty-box">
      Оформленных заказов пока нет.
    </div>

    <template v-else>
      <div class="order-top-filters">
        <div class="order-search-wrap">
          <input
            v-model="orderSearchQuery"
            type="text"
            class="admin-search-input"
            placeholder="Поиск по № заказа (СТ-0001), фамилии, телефону, компании или УНП..."
          />
          <button
            v-if="orderSearchQuery"
            type="button"
            class="btn-clear-order-search"
            title="Очистить поиск"
            @click="orderSearchQuery = ''"
          >
            <X :size="14" />
          </button>
        </div>

        <div class="role-segment-group">
          <button
            type="button"
            class="role-seg-btn"
            :class="{ active: selectedOrderRole === 'all' }"
            @click="selectedOrderRole = 'all'"
          >
            Все клиенты
          </button>
          <button
            type="button"
            class="role-seg-btn"
            :class="{ active: selectedOrderRole === 'wholesale' }"
            @click="selectedOrderRole = 'wholesale'"
          >
            <Building2 :size="14" /> Опт (Юрлица)
          </button>
          <button
            type="button"
            class="role-seg-btn"
            :class="{ active: selectedOrderRole === 'retail' }"
            @click="selectedOrderRole = 'retail'"
          >
            <ShoppingBag :size="14" /> Розница
          </button>
        </div>
      </div>

      <div class="order-filters-bar">
        <button
          v-for="filter in orderStatusFilters"
          :key="filter.value"
          type="button"
          class="filter-pill-btn"
          :class="{ active: selectedOrderStatus === filter.value }"
          @click="selectedOrderStatus = filter.value"
        >
          <component :is="filter.icon" :size="14" />
          <span>{{ filter.label }}</span>
          <span class="filter-pill-count">{{ orderCountsByStatus[filter.value] || 0 }}</span>
        </button>
      </div>

      <div v-if="filteredAdminOrders.length === 0" class="empty-box">
        <p>По выбранным параметрам заказов не найдено.</p>
        <button type="button" class="btn-reset-orders" @click="resetOrderFilters">
          Сбросить фильтры
        </button>
      </div>

      <div v-else class="orders-admin-list">
        <article v-for="order in filteredAdminOrders" :key="order.id" class="order-admin-card">
          <div class="order-admin-head">
            <div>
              <strong class="order-num">Заказ №{{ order.number }}</strong>
              <span class="order-date">от {{ order.createdAt }}</span>
              <span class="role-badge" :class="order.role">
                {{ order.role === 'wholesale' ? `🏢 Опт (${order.companyName || 'УНП ' + order.unp})` : '🛍️ Розница' }}
              </span>
            </div>
            <div class="order-sum">{{ formatPrice(order.products_total_byn) }} BYN</div>
          </div>

          <div class="order-client-info">
            <div><strong>Получатель:</strong> {{ order.recipient.full_name }} • {{ order.recipient.phone }}</div>
            <div>
              <strong>Доставка:</strong>
              <template v-if="order.delivery.method === 'europost'">
                Европочта (г. {{ order.delivery.city }}, {{ order.delivery.office }})
              </template>
              <template v-else-if="order.delivery.method === 'manager'">
                Опт (обсуждается с менеджером)
              </template>
              <template v-else>
                Самовывоз (ЭКСПОБЕЛ, пав. 218/219)
              </template>
            </div>
            <div v-if="order.comment"><strong>Комментарий:</strong> {{ order.comment }}</div>
          </div>

          <ul class="order-items-mini">
            <li v-for="item in order.items" :key="item.product_id">
              [{{ item.sku }}] {{ item.name }} — <strong>{{ item.quantity }} шт.</strong> × {{ formatPrice(item.unit_price) }} BYN
            </li>
          </ul>

          <div v-if="orderDrafts[order.id]" class="order-controls">
            <div class="control-group">
              <label>Статус заказа:</label>
              <select v-model="orderDrafts[order.id].status" class="admin-select">
                <option value="processing">В обработке</option>
                <option value="europost_pending">Уточняется доставка Европочтой</option>
                <option value="shipped">Отправлено Европочтой</option>
                <option value="ready_pickup">Готово к самовывозу (ЭКСПОБЕЛ)</option>
                <option value="completed">Выполнено (в архив)</option>
                <option value="cancelled">Отменён (возврат на склад)</option>
              </select>
            </div>

            <div class="control-group">
              <label>Трек-код Европочты:</label>
              <input
                v-model="orderDrafts[order.id].trackCode"
                type="text"
                class="admin-input"
                placeholder="Например: BY123456789"
              />
            </div>

            <button type="button" class="btn-save-order" @click="emit('save-order', order.id)">
              Сохранить
            </button>
            <button
              type="button"
              class="btn-icon del"
              title="Удалить заказ"
              @click="emit('delete-order', { order, fromArchive: false })"
            >
              <Trash2 :size="15" />
            </button>
          </div>
        </article>
      </div>

      <div v-if="hasMore" style="text-align: center; margin-top: 16px;">
        <button
          type="button"
          class="btn-save-order"
          :disabled="isLoadingMore"
          @click="emit('load-more')"
        >
          {{ isLoadingMore ? 'Загрузка...' : 'Загрузить ещё заказы' }}
        </button>
      </div>
    </template>
  </div>
</template>
