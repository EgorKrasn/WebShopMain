<script setup>
import { ref, computed } from 'vue'
import { Trash2, X } from 'lucide-vue-next'
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

const archiveSearchQuery = ref('')
const archiveStatusFilter = ref('all')

const filteredArchiveOrders = computed(() => {
  const q = archiveSearchQuery.value.trim().toLowerCase()
  return props.orders.filter((order) => {
    const matchesStatus =
      archiveStatusFilter.value === 'all' || order.status === archiveStatusFilter.value
    if (!matchesStatus) return false
    if (!q) return true

    return (
      (order.number || '').toLowerCase().includes(q) ||
      (order.recipient?.full_name || '').toLowerCase().includes(q) ||
      (order.recipient?.phone || '').toLowerCase().includes(q) ||
      (order.companyName || '').toLowerCase().includes(q) ||
      (order.unp || '').toLowerCase().includes(q)
    )
  })
})

const formatPrice = (value) => {
  return Number(value || 0).toFixed(2).replace('.', ',')
}
</script>

<template>
  <div class="tab-content">
    <div class="order-top-filters">
      <div class="order-search-wrap">
        <input
          v-model="archiveSearchQuery"
          type="text"
          class="admin-search-input"
          placeholder="Поиск в архиве по № заказа, ФИО, телефону, компании или УНП..."
        />
        <button
          v-if="archiveSearchQuery"
          type="button"
          class="btn-clear-order-search"
          @click="archiveSearchQuery = ''"
        >
          <X :size="14" />
        </button>
      </div>

      <div class="role-segment-group">
        <button
          type="button"
          class="role-seg-btn"
          :class="{ active: archiveStatusFilter === 'all' }"
          @click="archiveStatusFilter = 'all'"
        >
          Весь архив ({{ orders.length }})
        </button>
        <button
          type="button"
          class="role-seg-btn"
          :class="{ active: archiveStatusFilter === 'completed' }"
          @click="archiveStatusFilter = 'completed'"
        >
          Выполненные
        </button>
        <button
          type="button"
          class="role-seg-btn"
          :class="{ active: archiveStatusFilter === 'cancelled' }"
          @click="archiveStatusFilter = 'cancelled'"
        >
          Отменённые
        </button>
      </div>
    </div>

    <div v-if="filteredArchiveOrders.length === 0" class="empty-box">
      В архиве пока нет заявок по выбранным условиям.
    </div>

    <div v-else class="orders-admin-list">
      <article v-for="order in filteredArchiveOrders" :key="order.id" class="order-admin-card">
        <div class="order-admin-head">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <strong class="order-num">Заказ №{{ order.number }}</strong>
            <span class="order-date">от {{ order.createdAt }}</span>
            <span class="role-badge" :class="order.role">
              {{ order.role === 'wholesale' ? `Опт (${order.companyName || 'УНП ' + order.unp})` : 'Розница' }}
            </span>
            <span
              class="status-pill"
              :class="order.status === 'cancelled' ? 'rejected' : 'approved'"
            >
              {{ order.status === 'cancelled' ? 'Отменён (товар возвращён)' : 'Выполнено' }}
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
          <div v-if="order.trackCode"><strong>Трек-код:</strong> {{ order.trackCode }}</div>
          <div v-if="order.comment"><strong>Комментарий:</strong> {{ order.comment }}</div>
        </div>

        <ul class="order-items-mini">
          <li v-for="item in order.items" :key="item.product_id">
            [{{ item.sku }}] {{ item.name }} — <strong>{{ item.quantity }} шт.</strong> × {{ formatPrice(item.unit_price) }} BYN
          </li>
        </ul>

        <div v-if="orderDrafts[order.id]" class="order-controls">
          <div class="control-group">
            <label>Изменить статус (вернуть в работу):</label>
            <select v-model="orderDrafts[order.id].status" class="admin-select">
              <option value="completed">Выполнено</option>
              <option value="cancelled">Отменён</option>
              <option value="processing">Вернуть в работу (В обработке)</option>
            </select>
          </div>

          <button type="button" class="btn-save-order" @click="emit('save-order', order.id)">
            Сохранить
          </button>
          <button
            type="button"
            class="btn-icon del"
            title="Удалить запись из архива"
            @click="emit('delete-order', { order, fromArchive: true })"
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
        {{ isLoadingMore ? 'Загрузка...' : 'Загрузить ещё из архива' }}
      </button>
    </div>
  </div>
</template>
