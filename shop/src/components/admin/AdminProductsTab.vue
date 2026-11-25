<script setup>
import { ref, computed, watch } from 'vue'
import {
  Save,
  Pencil,
  Copy,
  Trash2,
  Palette,
  X,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  CheckCheck
} from 'lucide-vue-next'
import AdminProductModal from './AdminProductModal.vue'
import { api, resolveImageUrl } from '../../services/api.js'
import './admin.css'

const props = defineProps({
  products: {
    type: Array,
    default: () => []
  },
  categories: {
    type: Array,
    default: () => []
  },
  quickDrafts: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['updated', 'toast', 'error'])

const productSearch = ref('')
const selectedCategory = ref('')
const selectedSubcategory = ref('')
const activeStockChip = ref('all') // 'all' | 'zero' | 'low' | 'promo' | 'no_image'
const activeGroupFilter = ref('')
const sortBy = ref('default') // 'default' | 'stock_asc' | 'stock_desc' | 'price_asc' | 'price_desc'

const PAGE_SIZE = 40
const currentPage = ref(1)

const isBulkSaving = ref(false)

const isModalOpen = ref(false)
const modalMode = ref('create')
const modalProduct = ref(null)

const openCreateProductModal = () => {
  modalMode.value = 'create'
  modalProduct.value = null
  isModalOpen.value = true
}

const openEditProductModal = (product) => {
  modalMode.value = 'edit'
  modalProduct.value = product
  isModalOpen.value = true
}

const openDuplicateProductModal = (product) => {
  modalMode.value = 'duplicate'
  modalProduct.value = product
  isModalOpen.value = true
}

const filterSubcategories = computed(() => {
  if (!selectedCategory.value) return []
  const found = props.categories.find((c) => c.name === selectedCategory.value)
  return found?.subcategories || []
})

const baseMatchedProducts = computed(() => {
  const q = productSearch.value.trim().toLowerCase()
  const grp = activeGroupFilter.value.trim().toLowerCase()

  return props.products.filter((p) => {
    if (grp && String(p.groupId || '').trim().toLowerCase() !== grp) {
      return false
    }
    if (selectedCategory.value && p.category !== selectedCategory.value) {
      return false
    }
    if (selectedSubcategory.value && p.subcategory !== selectedSubcategory.value) {
      return false
    }
    if (!q) return true

    return (
      p.sku.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      (p.groupId && p.groupId.toLowerCase().includes(q)) ||
      (p.colorName && p.colorName.toLowerCase().includes(q))
    )
  })
})

const chipCounts = computed(() => {
  const list = baseMatchedProducts.value
  return {
    all: list.length,
    zero: list.filter((p) => (p.stock ?? 0) <= 0).length,
    low: list.filter((p) => (p.stock ?? 0) > 0 && (p.stock ?? 0) < 5).length,
    promo: list.filter((p) => (p.discountPercent ?? 0) > 0 || Boolean(p.promoLabel)).length,
    no_image: list.filter((p) => !p.image || !String(p.image).trim()).length
  }
})
const filteredAndSortedProducts = computed(() => {
  let list = baseMatchedProducts.value

  if (activeStockChip.value === 'zero') {
    list = list.filter((p) => (p.stock ?? 0) <= 0)
  } else if (activeStockChip.value === 'low') {
    list = list.filter((p) => (p.stock ?? 0) > 0 && (p.stock ?? 0) < 5)
  } else if (activeStockChip.value === 'promo') {
    list = list.filter((p) => (p.discountPercent ?? 0) > 0 || Boolean(p.promoLabel))
  } else if (activeStockChip.value === 'no_image') {
    list = list.filter((p) => !p.image || !String(p.image).trim())
  }

  if (sortBy.value === 'default') return list

  const copy = [...list]
  if (sortBy.value === 'stock_asc') {
    copy.sort((a, b) => (a.stock ?? 0) - (b.stock ?? 0))
  } else if (sortBy.value === 'stock_desc') {
    copy.sort((a, b) => (b.stock ?? 0) - (a.stock ?? 0))
  } else if (sortBy.value === 'price_asc') {
    copy.sort((a, b) => (a.retailPrice ?? 0) - (b.retailPrice ?? 0))
  } else if (sortBy.value === 'price_desc') {
    copy.sort((a, b) => (b.retailPrice ?? 0) - (a.retailPrice ?? 0))
  }
  return copy
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredAndSortedProducts.value.length / PAGE_SIZE))
})

const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredAndSortedProducts.value.slice(start, start + PAGE_SIZE)
})

const visiblePageNumbers = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const pages = []
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - 2 && i <= current + 2)) {
      pages.push(i)
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...')
    }
  }
  return pages
})

watch(
  [productSearch, selectedCategory, selectedSubcategory, activeStockChip, activeGroupFilter, sortBy],
  () => {
    currentPage.value = 1
  }
)

watch(totalPages, (newTotal) => {
  if (currentPage.value > newTotal) {
    currentPage.value = newTotal
  }
})

const filterByGroup = (groupId) => {
  activeGroupFilter.value = groupId
  activeStockChip.value = 'all'
}

const resetAllFilters = () => {
  productSearch.value = ''
  selectedCategory.value = ''
  selectedSubcategory.value = ''
  activeStockChip.value = 'all'
  activeGroupFilter.value = ''
  sortBy.value = 'default'
}

const hasActiveFilters = computed(() => {
  return Boolean(
    productSearch.value.trim() ||
      selectedCategory.value ||
      selectedSubcategory.value ||
      activeStockChip.value !== 'all' ||
      activeGroupFilter.value ||
      sortBy.value !== 'default'
  )
})

const isRowDirty = (product) => {
  const draft = props.quickDrafts[product.id]
  if (!draft) return false
  return (
    Number(draft.retailPrice) !== Number(product.retailPrice) ||
    Number(draft.wholesalePrice) !== Number(product.wholesalePrice) ||
    Number(draft.stock) !== Number(product.stock ?? 0)
  )
}

const dirtyProducts = computed(() => {
  return props.products.filter((p) => isRowDirty(p))
})

const discardQuickDrafts = () => {
  for (const p of dirtyProducts.value) {
    if (props.quickDrafts[p.id]) {
      props.quickDrafts[p.id].retailPrice = p.retailPrice
      props.quickDrafts[p.id].wholesalePrice = p.wholesalePrice
      props.quickDrafts[p.id].stock = p.stock ?? 0
    }
  }
}

const saveQuickProductRow = async (productId) => {
  const draft = props.quickDrafts[productId]
  if (!draft) return
  emit('error', '')
  try {
    await api.adminUpdateProduct(productId, {
      retailPrice: Number(draft.retailPrice),
      wholesalePrice: Number(draft.wholesalePrice),
      stock: Number(draft.stock)
    })
    const target = props.products.find((p) => p.id === productId)
    if (target) {
      target.retailPrice = Number(draft.retailPrice)
      target.wholesalePrice = Number(draft.wholesalePrice)
      target.stock = Number(draft.stock)
    }
    emit('toast', 'Цена и остаток обновлены')
  } catch (err) {
    emit('error', err.message || 'Ошибка обновления товара')
  }
}

const saveAllDirtyProducts = async () => {
  const targets = dirtyProducts.value
  if (targets.length === 0) return

  isBulkSaving.value = true
  emit('error', '')
  try {
    await Promise.all(
      targets.map((p) => {
        const draft = props.quickDrafts[p.id]
        return api.adminUpdateProduct(p.id, {
          retailPrice: Number(draft.retailPrice),
          wholesalePrice: Number(draft.wholesalePrice),
          stock: Number(draft.stock)
        })
      })
    )

    for (const p of targets) {
      const draft = props.quickDrafts[p.id]
      p.retailPrice = Number(draft.retailPrice)
      p.wholesalePrice = Number(draft.wholesalePrice)
      p.stock = Number(draft.stock)
    }

    emit('toast', `Успешно сохранено изменений: ${targets.length} поз.`)
  } catch (err) {
    emit('error', err.message || 'Ошибка при массовом сохранении')
  } finally {
    isBulkSaving.value = false
  }
}

const deleteProductItem = async (product) => {
  if (!confirm(`Удалить товар «${product.name}» (${product.sku})?`)) return
  emit('error', '')
  try {
    await api.adminDeleteProduct(product.id)
    emit('updated')
    emit('toast', 'Товар удалён')
  } catch (err) {
    emit('error', err.message || 'Ошибка удаления товара')
  }
}
</script>

<template>
  <div class="tab-content">
    <div class="products-toolbar">
      <div class="order-search-wrap">
        <input
          v-model="productSearch"
          type="text"
          class="admin-search-input"
          placeholder="Поиск по артикулу, названию, цвету или группе..."
        />
        <button
          v-if="productSearch"
          type="button"
          class="btn-clear-order-search"
          title="Очистить поиск"
          @click="productSearch = ''"
        >
          <X :size="14" />
        </button>
      </div>

      <button type="button" class="btn-add-product" @click="openCreateProductModal">
        + Добавить товар
      </button>
    </div>

    <div class="products-filter-row">
      <select
        v-model="selectedCategory"
        class="admin-select"
        @change="selectedSubcategory = ''"
      >
        <option value="">Все категории</option>
        <option v-for="c in categories" :key="c.id" :value="c.name">
          {{ c.name }}
        </option>
      </select>

      <select
        v-if="filterSubcategories.length > 0"
        v-model="selectedSubcategory"
        class="admin-select"
      >
        <option value="">Все подкатегории</option>
        <option v-for="sub in filterSubcategories" :key="sub" :value="sub">
          {{ sub }}
        </option>
      </select>

      <select v-model="sortBy" class="admin-select">
        <option value="default">Сортировка: по умолчанию</option>
        <option value="stock_asc">Остаток: сначала меньше</option>
        <option value="stock_desc">Остаток: сначала больше</option>
        <option value="price_asc">Розница: дешевле -> дороже</option>
        <option value="price_desc">Розница: дороже -> дешевле</option>
      </select>

      <button
        v-if="hasActiveFilters"
        type="button"
        class="btn-reset-filters-inline"
        @click="resetAllFilters"
      >
        <RotateCcw :size="14" />
        <span>Сбросить фильтры</span>
      </button>
    </div>

    <div class="order-filters-bar">
      <button
        type="button"
        class="filter-pill-btn"
        :class="{ active: activeStockChip === 'all' }"
        @click="activeStockChip = 'all'"
      >
        <span>Все</span>
        <span class="filter-pill-count">{{ chipCounts.all }}</span>
      </button>

      <button
        type="button"
        class="filter-pill-btn"
        :class="{ active: activeStockChip === 'zero' }"
        @click="activeStockChip = 'zero'"
      >
        <span>Нет в наличии (0)</span>
        <span class="filter-pill-count">{{ chipCounts.zero }}</span>
      </button>

      <button
        type="button"
        class="filter-pill-btn"
        :class="{ active: activeStockChip === 'low' }"
        @click="activeStockChip = 'low'"
      >
        <span>Мало (&lt; 5 шт.)</span>
        <span class="filter-pill-count">{{ chipCounts.low }}</span>
      </button>

      <button
        type="button"
        class="filter-pill-btn"
        :class="{ active: activeStockChip === 'promo' }"
        @click="activeStockChip = 'promo'"
      >
        <span>Со скидкой</span>
        <span class="filter-pill-count">{{ chipCounts.promo }}</span>
      </button>

      <button
        type="button"
        class="filter-pill-btn"
        :class="{ active: activeStockChip === 'no_image' }"
        @click="activeStockChip = 'no_image'"
      >
        <span>Без фото</span>
        <span class="filter-pill-count">{{ chipCounts.no_image }}</span>
      </button>
    </div>

    <div v-if="activeGroupFilter" class="group-filter-banner">
      <div style="display: flex; align-items: center; gap: 8px;">
        <Palette :size="16" />
        <span>
          Показаны все расцветки группы: <strong>{{ activeGroupFilter }}</strong>
          ({{ filteredAndSortedProducts.length }} шт.)
        </span>
      </div>
      <button type="button" class="btn-clear-group" @click="activeGroupFilter = ''">
        <X :size="14" />
        <span>Показать весь каталог</span>
      </button>
    </div>

    <div v-if="dirtyProducts.length > 0" class="bulk-save-bar">
      <div class="bulk-save-info">
        Несохранённые правки в строках: <strong>{{ dirtyProducts.length }}</strong>
      </div>
      <div class="bulk-save-actions">
        <button
          type="button"
          class="btn-discard-bulk"
          :disabled="isBulkSaving"
          @click="discardQuickDrafts"
        >
          Отменить правки
        </button>
        <button
          type="button"
          class="btn-save-bulk"
          :disabled="isBulkSaving"
          @click="saveAllDirtyProducts"
        >
          <CheckCheck :size="16" />
          <span>
            {{ isBulkSaving ? 'Сохранение...' : `Сохранить все изменения (${dirtyProducts.length})` }}
          </span>
        </button>
      </div>
    </div>
    <div v-if="filteredAndSortedProducts.length === 0" class="empty-box">
      <p>По заданным фильтрам товары не найдены.</p>
      <button v-if="hasActiveFilters" type="button" class="btn-reset-orders" @click="resetAllFilters">
        Сбросить фильтры
      </button>
    </div>

    <template v-else>
      <div class="products-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Артикул / Группа</th>
              <th>Товар</th>
              <th>Розница (BYN)</th>
              <th>Опт (BYN)</th>
              <th>Остаток (шт.)</th>
              <th>Действия</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="p in paginatedProducts"
              :key="p.id"
              :class="{ 'row-dirty': isRowDirty(p) }"
            >
              <td>
                <strong>{{ p.sku }}</strong>
                <div v-if="p.groupId" class="group-cell-box">
                  <span class="sub-text">Группа: {{ p.groupId }}</span>
                  <button
                    v-if="activeGroupFilter !== p.groupId"
                    type="button"
                    class="btn-group-filter"
                    title="Показать все расцветки этой модели"
                    @click="filterByGroup(p.groupId)"
                  >
                    Все цвета группы
                  </button>
                </div>
              </td>
              <td>
                <div class="prod-cell">
                  <img
                    v-if="p.image"
                    :src="resolveImageUrl(p.image)"
                    loading="lazy"
                    class="mini-thumb"
                    alt=""
                  />
                  <div>
                    <strong>{{ p.name }}</strong>
                    <span v-if="p.colorName" class="admin-color-tag">
                      {{ p.colorName }}
                    </span>
                    <span v-if="p.discountPercent > 0 || p.promoLabel" class="admin-promo-tag">
                      {{ p.promoLabel || `-${p.discountPercent}%` }}
                    </span>
                    <div class="sub-text">
                      {{ p.category }}<template v-if="p.subcategory"> • {{ p.subcategory }}</template>
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <input
                  v-if="quickDrafts[p.id]"
                  v-model.number="quickDrafts[p.id].retailPrice"
                  type="number"
                  step="0.01"
                  class="num-input"
                />
              </td>
              <td>
                <input
                  v-if="quickDrafts[p.id]"
                  v-model.number="quickDrafts[p.id].wholesalePrice"
                  type="number"
                  step="0.01"
                  class="num-input"
                />
              </td>
              <td>
                <input
                  v-if="quickDrafts[p.id]"
                  v-model.number="quickDrafts[p.id].stock"
                  type="number"
                  min="0"
                  class="num-input"
                  :class="{ 'zero-stock': quickDrafts[p.id].stock <= 0 }"
                />
              </td>
              <td>
                <div class="row-actions">
                  <button
                    type="button"
                    class="btn-icon save"
                    title="Сохранить цену и остаток"
                    @click="saveQuickProductRow(p.id)"
                  >
                    <Save :size="15" />
                  </button>
                  <button
                    type="button"
                    class="btn-icon edit"
                    title="Редактировать карточку и характеристики"
                    @click="openEditProductModal(p)"
                  >
                    <Pencil :size="15" />
                  </button>
                  <button
                    type="button"
                    class="btn-icon copy"
                    title="Дублировать карточку товара"
                    @click="openDuplicateProductModal(p)"
                  >
                    <Copy :size="15" />
                  </button>
                  <button
                    type="button"
                    class="btn-icon del"
                    title="Удалить товар"
                    @click="deleteProductItem(p)"
                  >
                    <Trash2 :size="15" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="totalPages > 1" class="admin-pagination">
        <span class="pagination-info">
          Показано {{ (currentPage - 1) * PAGE_SIZE + 1 }}–{{ Math.min(currentPage * PAGE_SIZE, filteredAndSortedProducts.length) }}
          из {{ filteredAndSortedProducts.length }}
        </span>

        <div class="pagination-controls">
          <button
            type="button"
            class="page-btn"
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <ChevronLeft :size="16" />
          </button>

          <template v-for="(page, idx) in visiblePageNumbers" :key="idx">
            <span v-if="page === '...'" class="page-dots">...</span>
            <button
              v-else
              type="button"
              class="page-btn"
              :class="{ active: currentPage === page }"
              @click="currentPage = page"
            >
              {{ page }}
            </button>
          </template>

          <button
            type="button"
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            <ChevronRight :size="16" />
          </button>
        </div>
      </div>
    </template>

    <AdminProductModal
      :is-open="isModalOpen"
      :mode="modalMode"
      :product="modalProduct"
      :categories="categories"
      :all-products="products"
      @close="isModalOpen = false"
      @saved="emit('updated')"
      @toast="emit('toast', $event)"
      @error="emit('error', $event)"
    />
  </div>
</template>

<style scoped>
.products-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  align-items: center;
}

.btn-reset-filters-inline {
  height: 38px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-reset-filters-inline:hover {
  border-color: #0f172a;
  color: #0f172a;
}

.group-filter-banner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  margin-bottom: 14px;
  border-radius: 12px;
  background-color: #e0f2fe;
  border: 1.5px solid #38bdf8;
  color: #0369a1;
  font-size: 13px;
}

.btn-clear-group {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid #0284c7;
  background-color: #ffffff;
  color: #0369a1;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.bulk-save-bar {
  position: sticky;
  top: 12px;
  z-index: 50;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 14px;
  border-radius: 14px;
  background-color: #0f172a;
  color: #ffffff;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.25);
}

.bulk-save-info {
  font-size: 13.5px;
}

.bulk-save-info strong {
  color: #fbbf24;
  font-size: 15px;
}

.bulk-save-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-discard-bulk {
  height: 36px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: transparent;
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-save-bulk {
  height: 36px;
  padding: 0 16px;
  border-radius: 9px;
  border: none;
  background-color: #16a34a;
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.products-table-wrap {
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid #cbd5e1;
  overflow-x: auto;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.admin-table th,
.admin-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}

.admin-table th {
  background-color: #f8fafc;
  font-weight: 800;
  color: #475569;
}

.admin-table tr.row-dirty {
  background-color: #fffbeb;
}

.group-cell-box {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  margin-top: 2px;
}

.btn-group-filter {
  padding: 2px 7px;
  border-radius: 6px;
  border: 1px solid #bae6fd;
  background-color: #f0f9ff;
  color: #0284c7;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-group-filter:hover {
  background-color: #0284c7;
  border-color: #0284c7;
  color: #ffffff;
}

.prod-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-thumb {
  width: 38px;
  height: 38px;
  object-fit: contain;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.admin-color-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 7px;
  border-radius: 6px;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 11px;
  font-weight: 700;
}

.admin-promo-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 7px;
  border-radius: 6px;
  background-color: #fee2e2;
  color: #b91c1c;
  font-size: 11px;
  font-weight: 800;
}

.num-input {
  width: 82px;
  height: 34px;
  padding: 0 8px;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  font-weight: 700;
}

.num-input.zero-stock {
  border-color: #ef4444;
  background-color: #fef2f2;
  color: #b91c1c;
}

.admin-pagination {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: #ffffff;
  border-radius: 14px;
  border: 1px solid #cbd5e1;
}

.pagination-info {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.page-btn {
  min-width: 34px;
  height: 34px;
  padding: 0 8px;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.page-btn:hover:not(:disabled) {
  border-color: #0f172a;
}

.page-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-dots {
  color: #64748b;
  font-weight: 700;
  padding: 0 4px;
}
</style>
