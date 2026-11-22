<script setup>
import { ref, reactive, computed, onMounted, markRaw, watch } from 'vue'

import { useRoute, useRouter } from 'vue-router'

import { api, resolveImageUrl } from '../services/api.js'
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
  Clock,
  CheckCircle2,
  XCircle,
  LayoutGrid,
  Truck,
  Store,
  ShoppingBag,
  Trash2,
  Save,
  Pencil,
  Upload,
  X
} from 'lucide-vue-next'

import CategoryIcon from './CategoryIcon.vue'

import { useBackdropClose } from '../composables/useBackdropClose.js'




// Доступные векторные иконки для выбора при создании/редактировании категории
const categoryIconOptions = [
  { key: 'watch', label: 'Наручные' },
  { key: 'clock', label: 'Настенные' },
  { key: 'alarm', label: 'Будильники' },
  { key: 'weather', label: 'Метео' },
  { key: 'electronics', label: 'Электроника' },
  { key: 'radio', label: 'Радио' },
  { key: 'accessories', label: 'Аксессуары' },
  { key: 'gift', label: 'Подарки' }
]


const emit = defineEmits(['close'])

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


const categoryBackdrop = useBackdropClose(() => { isCategoryFormOpen.value = false })
const productBackdrop = useBackdropClose(() => { isProductFormOpen.value = false })


const isLoading = ref(false)
const actionMessage = ref('')
const errorMessage = ref('')

const wholesaleRequests = ref([])
const allOrders = ref([])
const selectedOrderStatus = ref('all')
const selectedOrderRole = ref('all') // 'all' | 'wholesale' | 'retail'
const orderSearchQuery = ref('')

const orderStatusFilters = [
  { value: 'all', label: 'Все активные', icon: LayoutGrid },
  { value: 'processing', label: 'В обработке', icon: Clock },
  { value: 'europost_pending', label: 'Уточняется Европочта', icon: Package },
  { value: 'shipped', label: 'Отправлено', icon: Truck },
  { value: 'ready_pickup', label: 'Готово к самовывозу', icon: Store }
]


const archiveOrders = ref([])
const archiveTotalCount = ref(0)
const hasMoreArchive = ref(false)
const isLoadingMoreArchive = ref(false)
const archiveSearchQuery = ref('')
const archiveStatusFilter = ref('all') // 'all' | 'completed' | 'cancelled'



// Базовая фильтрация по поиску и типу клиента (чтобы счётчики статусов считались корректно)
const baseFilteredOrders = computed(() => {
  const q = orderSearchQuery.value.trim().toLowerCase()

  return allOrders.value.filter((order) => {
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


const allProducts = ref([])
const productSearch = ref('')

const orderDrafts = ref({})
const productQuickDrafts = ref({})

// Состояние модальной формы создания / редактирования товара
const isProductFormOpen = ref(false)
const editingProductId = ref(null)
const productForm = reactive({
  sku: '',
  groupId: '',
  colorName: '',
  category: 'Наручные часы',
  subcategory: '',
  name: '',
  specs: '',
  description: '',
  image: '',
  icon: '⌚',
  retailPrice: 0,
  wholesalePrice: 0,
  minWholesaleQty: 5,
  stock: 10,
  attributes: [
    { label: 'Механизм', value: 'Кварцевый' },
    { label: 'Материал', value: 'Пластик / Стекло' },
    { label: 'Гарантия', value: '12 месяцев' }
  ]
})

const pendingWholesaleCount = computed(() => {
  return wholesaleRequests.value.filter((u) => u.wholesaleStatus === 'pending').length
})

const outOfStockCount = computed(() => {
  return allProducts.value.filter((p) => (p.stock ?? 0) <= 0).length
})

// Единый реестр разделов админки — в будущем новые разделы добавляются просто сюда
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
])


const activeSectionTitle = computed(() => {
  const found = adminSections.value.find((s) => s.id === activeTab.value)
  return found ? found.title : ''
})



const filteredAdminProducts = computed(() => {
  const q = productSearch.value.trim().toLowerCase()
  if (!q) return allProducts.value
  return allProducts.value.filter(
    (p) =>
      p.sku.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      (p.groupId && p.groupId.toLowerCase().includes(q))
  )
})

const showToast = (msg) => {
  actionMessage.value = msg
  setTimeout(() => {
    actionMessage.value = ''
  }, 3000)
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
      selectedOrderStatus.value = 'all'
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
      allProducts.value = Array.isArray(productsRes.value) ? productsRes.value : []
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



onMounted(() => {
  loadAdminData()
})

// --- Юрлица ---
const handleWholesaleDecision = async (userId, decision) => {
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

// --- Заказы ---
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

    // Если была отмена или возврат из отмены — обновим остатки товаров
    if (draft.status === 'cancelled' || archiveIdx !== -1) {
      const freshProducts = await api.getProducts()
      if (Array.isArray(freshProducts)) {
        allProducts.value = freshProducts
        for (const p of freshProducts) {
          if (productQuickDrafts.value[p.id]) {
            productQuickDrafts.value[p.id].stock = p.stock ?? 0
          }
        }
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

// --- Товары и остатки ---
const saveQuickProductRow = async (productId) => {
  const draft = productQuickDrafts.value[productId]
  if (!draft) return
  errorMessage.value = ''
  try {
    await api.adminUpdateProduct(productId, {
      retailPrice: Number(draft.retailPrice),
      wholesalePrice: Number(draft.wholesalePrice),
      stock: Number(draft.stock)
    })
    const target = allProducts.value.find((p) => p.id === productId)
    if (target) {
      target.retailPrice = Number(draft.retailPrice)
      target.wholesalePrice = Number(draft.wholesalePrice)
      target.stock = Number(draft.stock)
    }
    showToast('Цена и остаток обновлены')
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка обновления товара'
  }
}

const openCreateProductModal = () => {
  editingProductId.value = null
  Object.assign(productForm, {
    sku: '',
    groupId: '',
    colorName: '',
    category: 'Интерьерные и настенные',
    subcategory: '',
    name: '',
    specs: '',
    description: '',
    image: '',
    icon: '⏰',
    retailPrice: 25,
    wholesalePrice: 16,
    minWholesaleQty: 10,
    stock: 20,
    attributes: [
      { label: 'Механизм', value: 'Кварцевый' },
      { label: 'Материал', value: 'Пластик' },
      { label: 'Гарантия', value: '12 месяцев' }
    ]
  })
  isProductFormOpen.value = true
}

const openEditProductModal = (product) => {
  editingProductId.value = product.id
  const existingAttrs =
    Array.isArray(product.attributes) && product.attributes.length > 0
      ? product.attributes.map((a) => ({ label: a.label, value: a.value }))
      : [
          { label: 'Механизм', value: product.mechanism || '' },
          { label: 'Материал', value: product.caseMaterial || '' },
          { label: 'Гарантия', value: product.warranty || '12 месяцев' }
        ]

  Object.assign(productForm, {
    sku: product.sku || '',
    groupId: product.groupId || '',
    colorName: product.colorName || '',
    category: product.category || 'Наручные часы',
    subcategory: product.subcategory || '',
    name: product.name || '',
    specs: product.specs || '',
    description: product.description || '',
    image: product.image || '',
    icon: product.icon || '⌚',
    retailPrice: product.retailPrice || 0,
    wholesalePrice: product.wholesalePrice || 0,
    minWholesaleQty: product.minWholesaleQty || 5,
    stock: product.stock ?? 0,
    attributes: existingAttrs
  })
  isProductFormOpen.value = true
}

const addAttributeRow = () => {
  productForm.attributes.push({ label: '', value: '' })
}

const removeAttributeRow = (index) => {
  productForm.attributes.splice(index, 1)
}

const submitProductForm = async () => {
  errorMessage.value = ''
  const cleanAttributes = productForm.attributes
    .filter((a) => a.label.trim() && a.value.trim())
    .map((a) => ({ label: a.label.trim(), value: a.value.trim() }))

  const payload = {
    sku: productForm.sku,
    groupId: productForm.groupId,
    colorName: productForm.colorName,
    category: productForm.category,
    subcategory: productForm.subcategory,
    name: productForm.name,
    specs: productForm.specs,
    description: productForm.description,
    image: productForm.image,
    icon: productForm.icon,
    retailPrice: Number(productForm.retailPrice),
    wholesalePrice: Number(productForm.wholesalePrice),
    minWholesaleQty: Number(productForm.minWholesaleQty),
    stock: Number(productForm.stock),
    attributes: cleanAttributes
  }

  try {
    if (editingProductId.value) {
      await api.adminUpdateProduct(editingProductId.value, payload)
      showToast('Товар успешно обновлён')
    } else {
      await api.adminCreateProduct(payload)
      showToast('Новый товар добавлен в каталог')
    }
    isProductFormOpen.value = false
    await loadAdminData()
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка сохранения товара'
  }
}

const deleteProductItem = async (product) => {
  if (!confirm(`Удалить товар «${product.name}» (${product.sku})?`)) return
  errorMessage.value = ''
  try {
    await api.adminDeleteProduct(product.id)
    allProducts.value = allProducts.value.filter((p) => p.id !== product.id)
    showToast('Товар удалён')
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка удаления товара'
  }
}

const formatPrice = (value) => {
  return Number(value || 0).toFixed(2).replace('.', ',')
}

const isUploadingImage = ref(false)

const handleImageFileUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  isUploadingImage.value = true
  errorMessage.value = ''
  try {
    const res = await api.adminUploadImage(file)
    if (res?.url) {
      productForm.image = res.url
      showToast('Фото загружено')
    }
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось загрузить фото'
  } finally {
    isUploadingImage.value = false
    event.target.value = ''
  }
}

const allCategories = ref([])
const isCategoryFormOpen = ref(false)
const editingCategoryId = ref(null)
const categoryForm = reactive({
  name: '',
  icon: '⌚',
  sortOrder: 0,
  subcategories: ['']
})

const openCreateCategoryModal = () => {
  editingCategoryId.value = null
  Object.assign(categoryForm, {
    name: '',
    icon: 'watch',
    sortOrder: allCategories.value.length + 1,
    subcategories: ['']
  })
  isCategoryFormOpen.value = true
}

const openEditCategoryModal = (cat) => {
  editingCategoryId.value = cat.id
  Object.assign(categoryForm, {
    name: cat.name,
    icon: cat.icon || '⌚',
    sortOrder: cat.sortOrder || 0,
    subcategories: Array.isArray(cat.subcategories) && cat.subcategories.length > 0
      ? [...cat.subcategories]
      : ['']
  })
  isCategoryFormOpen.value = true
}

const addSubcategoryRow = () => {
  categoryForm.subcategories.push('')
}

const removeSubcategoryRow = (idx) => {
  categoryForm.subcategories.splice(idx, 1)
}

const submitCategoryForm = async () => {
  errorMessage.value = ''
  const payload = {
    name: categoryForm.name,
    icon: categoryForm.icon,
    sortOrder: Number(categoryForm.sortOrder),
    subcategories: categoryForm.subcategories.filter((s) => s.trim())
  }
  try {
    if (editingCategoryId.value) {
      await api.adminUpdateCategory(editingCategoryId.value, payload)
      showToast('Категория обновлена')
    } else {
      await api.adminCreateCategory(payload)
      showToast('Категория создана')
    }
    isCategoryFormOpen.value = false
    await loadAdminData()
    emit('categories-updated')
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка сохранения категории'
  }
}

const deleteCategoryItem = async (cat) => {
  if (!confirm(`Удалить категорию «${cat.name}»?`)) return
  errorMessage.value = ''
  try {
    await api.adminDeleteCategory(cat.id)
    await loadAdminData()
    emit('categories-updated')
    showToast('Категория удалена')
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка удаления категории'
  }
}

const availableSubcategories = computed(() => {
  const found = allCategories.value.find((c) => c.name === productForm.category)
  return found?.subcategories || []
})

const ordersTotalCount = ref(0)
const hasMoreOrders = ref(false)
const isLoadingMoreOrders = ref(false)
const ORDERS_PAGE_SIZE = 20

const fillOrderDrafts = (ordersArray) => {
  const updated = { ...orderDrafts.value }
  for (const o of ordersArray) {
    updated[o.id] = { status: o.status, trackCode: o.trackCode || '' }
  }
  orderDrafts.value = updated
}

const fetchOrdersList = async (reset = true) => {
  const mode = selectedOrderStatus.value === 'completed' ? 'completed' : 'active'
  const offset = reset ? 0 : allOrders.value.length

  if (!reset) isLoadingMoreOrders.value = true
  try {
    const res = await api.adminGetOrders(mode, ORDERS_PAGE_SIZE, offset)
    const loadedItems = Array.isArray(res?.items) ? res.items : []
    allOrders.value = reset ? loadedItems : [...allOrders.value, ...loadedItems]
    ordersTotalCount.value = res?.total ?? allOrders.value.length
    hasMoreOrders.value = Boolean(res?.hasMore)
    fillOrderDrafts(loadedItems)
  } finally {
    isLoadingMoreOrders.value = false
  }
}

const handleSelectOrderStatus = async (newStatus) => {
  const wasCompleted = selectedOrderStatus.value === 'completed'
  const willBeCompleted = newStatus === 'completed'
  selectedOrderStatus.value = newStatus

  if (wasCompleted !== willBeCompleted) {
    await fetchOrdersList(true)
  }
}


const handleDeleteOrder = async (order, fromArchive = false) => {
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
      // Обновляем остатки на складе после возврата
      const freshProducts = await api.getProducts()
      if (Array.isArray(freshProducts)) {
        allProducts.value = freshProducts
        for (const p of freshProducts) {
          if (productQuickDrafts.value[p.id]) {
            productQuickDrafts.value[p.id].stock = p.stock ?? 0
          }
        }
      }
    }
    showToast(fromArchive ? 'Запись удалена из архива' : 'Заказ удалён, остатки возвращены на склад')
  } catch (err) {
    errorMessage.value = err.message || 'Не удалось удалить заказ'
  }
}

const filteredArchiveOrders = computed(() => {
  const q = archiveSearchQuery.value.trim().toLowerCase()
  return archiveOrders.value.filter((order) => {
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
        <button type="button" class="btn-refresh" @click="loadAdminData" :disabled="isLoading">
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

    <!-- ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ (ХАБ РАЗДЕЛОВ) -->
    <div v-else-if="activeTab === 'menu'" class="admin-hub">
      <!-- Быстрая сводка по магазину -->
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

      <!-- Сетка модулей админки -->
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

        <!-- Заготовка под будущие разделы -->
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


    <!-- ВКЛАДКА 1: ЗАЯВКИ ЮРЛИЦ -->
    <div v-else-if="activeTab === 'wholesale'" class="tab-content">
      <div v-if="wholesaleRequests.length === 0" class="empty-box">
        Заявок на подключение оптового аккаунта пока нет.
      </div>

      <div v-else class="cards-grid">
        <article
          v-for="user in wholesaleRequests"
          :key="user.id"
          class="admin-card"
          :class="{ 'is-pending': user.wholesaleStatus === 'pending' }"
        >
          <div class="card-header">
            <div>
              <strong class="company-title">{{ user.companyName || 'Без названия' }}</strong>
              <span class="unp-tag">УНП: {{ user.unp }}</span>
            </div>

            <span v-if="user.wholesaleStatus === 'pending'" class="status-pill pending">
              <Clock :size="13" /> Ожидает проверки
            </span>
            <span v-else-if="user.wholesaleStatus === 'approved'" class="status-pill approved">
              <CheckCircle2 :size="13" /> Опт одобрен
            </span>
            <span v-else class="status-pill rejected">
              <XCircle :size="13" /> Отклонено
            </span>

          </div>

          <div class="card-details">
            <div><strong>Контактное лицо:</strong> {{ user.fullName }}</div>
            <div><strong>Телефон:</strong> {{ user.phone }}</div>
            <div><strong>Email:</strong> {{ user.email }}</div>
            <div v-if="user.legalAddress"><strong>Юр. адрес:</strong> {{ user.legalAddress }}</div>
          </div>

          <div class="card-actions">
            <button
              v-if="user.wholesaleStatus !== 'approved'"
              type="button"
              class="btn-approve"
              @click="handleWholesaleDecision(user.id, 'approved')"
            >
              <CheckCircle2 :size="15" /> Одобрить опт
            </button>
            <button
              v-if="user.wholesaleStatus !== 'rejected'"
              type="button"
              class="btn-reject"
              @click="handleWholesaleDecision(user.id, 'rejected')"
            >
              <XCircle :size="15" /> Отклонить
            </button>

          </div>
        </article>
      </div>
    </div>

    <!-- ВКЛАДКА 2: ВСЕ ЗАКАЗЫ -->
    <div v-else-if="activeTab === 'orders'" class="tab-content">
      <div v-if="allOrders.length === 0" class="empty-box">
        Оформленных заказов пока нет.
      </div>

      <template v-else>
        <!-- Поиск и фильтр по типу клиента (Опт / Розница) -->
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
              ✕
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

        <!-- Панель фильтрации по статусам -->
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
          <!-- Карточки заказов остаются без изменений -->
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

              <button type="button" class="btn-save-order" @click="saveOrderChanges(order.id)">
                Сохранить
              </button>
              <button type="button" class="btn-icon del" title="Удалить заказ" @click="handleDeleteOrder(order)"><Trash2 :size="15" /></button>
            </div>
          </article>
        </div>
        <div v-if="hasMoreOrders" style="text-align: center; margin-top: 16px;">
          <button
            type="button"
            class="btn-save-order"
            :disabled="isLoadingMoreOrders"
            @click="fetchOrdersList(false)"
          >
            {{ isLoadingMoreOrders ? 'Загрузка...' : 'Загрузить ещё заказы' }}
          </button>
        </div>

      </template>

    </div>

    <!-- ВКЛАДКА 2.5: АРХИВ ВЫПОЛНЕННЫХ И ОТМЕНЁННЫХ ЗАЯВОК -->
    <div v-else-if="activeTab === 'archive'" class="tab-content">
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
            Весь архив ({{ archiveOrders.length }})
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

            <button type="button" class="btn-save-order" @click="saveOrderChanges(order.id)">
              Сохранить
            </button>
            <button
              type="button"
              class="btn-icon del"
              title="Удалить запись из архива"
              @click="handleDeleteOrder(order, true)"
            >
              <Trash2 :size="15" />
            </button>
          </div>
        </article>
      </div>

      <div v-if="hasMoreArchive" style="text-align: center; margin-top: 16px;">
        <button
          type="button"
          class="btn-save-order"
          :disabled="isLoadingMoreArchive"
          @click="fetchArchiveList(false)"
        >
          {{ isLoadingMoreArchive ? 'Загрузка...' : 'Загрузить ещё из архива' }}
        </button>
      </div>
    </div>


    <!-- ВКЛАДКА 3: ТОВАРЫ И ОСТАТКИ -->
    <div v-else-if="activeTab === 'products'" class="tab-content">
      <div class="products-toolbar">
        <input
          v-model="productSearch"
          type="text"
          class="admin-search-input"
          placeholder="Поиск по артикулу, названию или группе цвета..."
        />
        <button type="button" class="btn-add-product" @click="openCreateProductModal">
          + Добавить товар
        </button>
      </div>

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
            <tr v-for="p in filteredAdminProducts" :key="p.id">
              <td>
                <strong>{{ p.sku }}</strong>
                <div v-if="p.groupId" class="sub-text">Группа: {{ p.groupId }}</div>
              </td>
              <td>
                <div class="prod-cell">
                  <img v-if="p.image" :src="resolveImageUrl(p.image)" class="mini-thumb" alt="" />
                  <div>
                    <strong>{{ p.name }}</strong>
                    <div class="sub-text">{{ p.category }}</div>
                  </div>
                </div>
              </td>
              <td>
                <input
                  v-if="productQuickDrafts[p.id]"
                  v-model.number="productQuickDrafts[p.id].retailPrice"
                  type="number"
                  step="0.01"
                  class="num-input"
                />
              </td>
              <td>
                <input
                  v-if="productQuickDrafts[p.id]"
                  v-model.number="productQuickDrafts[p.id].wholesalePrice"
                  type="number"
                  step="0.01"
                  class="num-input"
                />
              </td>
              <td>
                <input
                  v-if="productQuickDrafts[p.id]"
                  v-model.number="productQuickDrafts[p.id].stock"
                  type="number"
                  min="0"
                  class="num-input"
                  :class="{ 'zero-stock': productQuickDrafts[p.id].stock <= 0 }"
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
    </div>

    <!-- ВКЛАДКА 4: КАТЕГОРИИ И ПОДКАТЕГОРИИ -->
    <div v-else-if="activeTab === 'categories'" class="tab-content">
      <div class="products-toolbar">
        <div style="font-size: 14px; color: #334155; font-weight: 600;">
          Управление разделами бокового меню каталога
        </div>
        <button type="button" class="btn-add-product" @click="openCreateCategoryModal">
          + Добавить категорию
        </button>
      </div>

      <div class="cards-grid">
        <article v-for="cat in allCategories" :key="cat.id" class="admin-card">
          <div class="card-header">
            <div>
              <strong class="company-title" style="display: inline-flex; align-items: center; gap: 8px;">
                <CategoryIcon :icon="cat.icon" :size="18" />
                <span>{{ cat.name }}</span>
              </strong>
              <span class="unp-tag">Порядок: {{ cat.sortOrder }}</span>
            </div>

            <div class="row-actions">
              <button type="button" class="btn-icon edit" title="Редактировать" @click="openEditCategoryModal(cat)">
                <Pencil :size="15" />
              </button>
              <button type="button" class="btn-icon del" title="Удалить" @click="deleteCategoryItem(cat)">
                <Trash2 :size="15" />
              </button>
            </div>
          </div>

          <div class="card-details">
            <strong>Подкатегории ({{ cat.subcategories?.length || 0 }}):</strong>
            <div v-if="cat.subcategories?.length" style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
              <span
                v-for="sub in cat.subcategories"
                :key="sub"
                style="background: #f1f5f9; padding: 3px 8px; border-radius: 6px; font-size: 12px;"
              >
                {{ sub }}
              </span>
            </div>
            <span v-else class="sub-text">Подкатегории не заданы</span>
          </div>
        </article>
      </div>
    </div>

    <!-- МОДАЛЬНОЕ ОКНО РЕДАКТОРА КАТЕГОРИИ -->
    <div v-if="isCategoryFormOpen" 
          class="modal-overlay" 
          @mousedown.self="categoryBackdrop.onBackdropMouseDown" 
          @mouseup.self="categoryBackdrop.onBackdropMouseUp">
      <form class="product-editor-modal" @submit.prevent="submitCategoryForm">
        <div class="editor-head">
          <h3>{{ editingCategoryId ? 'Редактирование категории' : 'Новая категория каталога' }}</h3>
          <button type="button" class="close-editor" @click="isCategoryFormOpen = false">✕</button>
        </div>


        <div class="editor-body">
          <div class="form-grid-2">
            <div class="f-group">
              <label>Название раздела *</label>
              <input v-model="categoryForm.name" type="text" required placeholder="Например: Настенные часы" />
            </div>
            <div class="f-group">
              <label>Порядок в меню</label>
              <input v-model.number="categoryForm.sortOrder" type="number" />
            </div>
          </div>

          <div class="f-group">
            <label>Иконка раздела</label>
            <div class="icon-picker-grid">
              <button
                v-for="opt in categoryIconOptions"
                :key="opt.key"
                type="button"
                class="icon-pick-btn"
                :class="{ active: categoryForm.icon === opt.key }"
                @click="categoryForm.icon = opt.key"
              >
                <CategoryIcon :icon="opt.key" :size="18" />
                <span>{{ opt.label }}</span>
              </button>
            </div>
          </div>


          <div class="attrs-editor">
            <div class="attrs-head">
              <label>Подкатегории (пункты справа в меню):</label>
              <button type="button" class="btn-add-attr" @click="addSubcategoryRow">+ Добавить пункт</button>
            </div>
            <div v-for="(sub, idx) in categoryForm.subcategories" :key="idx" class="attr-row" style="grid-template-columns: 1fr 32px;">
              <input v-model="categoryForm.subcategories[idx]" type="text" placeholder="Название подкатегории..." />
              <button type="button" class="btn-del-attr" @click="removeSubcategoryRow(idx)">✕</button>
            </div>
          </div>
        </div>

        <div class="editor-foot">
          <button type="button" class="btn-cancel" @click="isCategoryFormOpen = false">Отмена</button>
          <button type="submit" class="btn-submit-prod">Сохранить категорию</button>
        </div>
      </form>
    </div>


    <!-- МОДАЛЬНОЕ ОКНО СОЗДАНИЯ / РЕДАКТИРОВАНИЯ ТОВАРА -->
    <div v-if="isProductFormOpen" 
        class="modal-overlay" 
        @mousedown.self="productBackdrop.onBackdropMouseDown" 
        @mouseup.self="productBackdrop.onBackdropMouseUp">
      <form class="product-editor-modal" @submit.prevent="submitProductForm">
        <div class="editor-head">
          <h3>{{ editingProductId ? 'Редактирование товара' : 'Новый товар в каталог' }}</h3>
          <button type="button" class="close-editor" @click="isProductFormOpen = false">✕</button>
        </div>

        <div class="editor-body">
          <div class="f-group">
            <label>Артикул (SKU) *</label>
            <input v-model="productForm.sku" type="text" required placeholder="Например: ST-3306" />
          </div>

          <div class="form-grid-2">
            <div class="f-group">
              <label>Категория *</label>
              <select v-model="productForm.category" required @change="productForm.subcategory = ''">
                <option v-for="c in allCategories" :key="c.id" :value="c.name">
                  {{ c.name }}
                </option>
              </select>
            </div>
            <div class="f-group">
              <label>Подкатегория</label>
              <select v-model="productForm.subcategory" :disabled="availableSubcategories.length === 0">
                <option value="">— Без подкатегории —</option>
                <option v-for="sub in availableSubcategories" :key="sub" :value="sub">
                  {{ sub }}
                </option>
              </select>
            </div>
          </div>



          <div class="f-group">
            <label>Полное название товара *</label>
            <input v-model="productForm.name" type="text" required placeholder="Будильник настольный «Modern Square» (Белый)" />
          </div>

          <div class="form-grid-2">
            <div class="f-group">
              <label>ID группы цветов (для объединения вариантов)</label>
              <input v-model="productForm.groupId" type="text" placeholder="alarm-330" />
            </div>
            <div class="f-group">
              <label>Название цвета (для переключателя)</label>
              <input v-model="productForm.colorName" type="text" placeholder="Белый" />
            </div>
          </div>

          <div class="f-group">
            <label>Фотография товара</label>
            <div class="upload-row">
              <label class="btn-upload-file" style="gap: 6px;">
                <Upload :size="14" />
                <span>{{ isUploadingImage ? 'Загрузка...' : 'Выбрать файл с ПК' }}</span>
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  :disabled="isUploadingImage"
                  @change="handleImageFileUpload"
                />
              </label>

              <input
                v-model="productForm.image"
                type="text"
                placeholder="Или вставьте ссылку / путь к фото..."
              />
            </div>
            <img v-if="productForm.image" :src="resolveImageUrl(productForm.image)" class="editor-img-preview" alt="Предпросмотр" />
          </div>


          <div class="f-group">
            <label>Краткие характеристики (под заголовком в каталоге) *</label>
            <input v-model="productForm.specs" type="text" required placeholder="Широкий экран • Кварцевый механизм • AA" />
          </div>

          <div class="f-group">
            <label>Подробное описание</label>
            <textarea v-model="productForm.description" rows="2"></textarea>
          </div>

          <div class="form-grid-4">
            <div class="f-group">
              <label>Розница (BYN) *</label>
              <input v-model.number="productForm.retailPrice" type="number" step="0.01" required />
            </div>
            <div class="f-group">
              <label>Опт (BYN) *</label>
              <input v-model.number="productForm.wholesalePrice" type="number" step="0.01" required />
            </div>
            <div class="f-group">
              <label>Мин. опт (шт.)</label>
              <input v-model.number="productForm.minWholesaleQty" type="number" min="1" />
            </div>
            <div class="f-group">
              <label>Остаток (шт.)</label>
              <input v-model.number="productForm.stock" type="number" min="0" />
            </div>
          </div>

          <div class="attrs-editor">
            <div class="attrs-head">
              <label>Характеристики в карточке (названия полей можно менять):</label>
              <button type="button" class="btn-add-attr" @click="addAttributeRow">+ Добавить поле</button>
            </div>
            <div v-for="(attr, idx) in productForm.attributes" :key="idx" class="attr-row">
              <input v-model="attr.label" type="text" placeholder="Название поля (напр. Водозащита)" />
              <input v-model="attr.value" type="text" placeholder="Значение (напр. 5 ATM)" />
              <button type="button" class="btn-del-attr" @click="removeAttributeRow(idx)">✕</button>
            </div>
          </div>
        </div>

        <div class="editor-foot">
          <button type="button" class="btn-cancel" @click="isProductFormOpen = false">Отмена</button>
          <button type="submit" class="btn-submit-prod">Сохранить товар</button>
        </div>
      </form>
    </div>
   
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
.admin-tabs {
display: flex;
gap: 10px;
margin-bottom: 18px;
flex-wrap: wrap;
}
.tab-btn {
height: 42px;
padding: 0 18px;
border-radius: 12px;
border: 1.5px solid #cbd5e1;
background-color: #ffffff;
color: #334155;
font-size: 14px;
font-weight: 700;
cursor: pointer;
display: inline-flex;
align-items: center;
gap: 8px;
}
.tab-btn.active {
background-color: #0f172a;
border-color: #0f172a;
color: #A3D2F9;
}
.tab-badge {
background-color: #ef4444;
color: #ffffff;
font-size: 11px;
padding: 2px 7px;
border-radius: 999px;
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
.admin-loading,
.empty-box {
padding: 40px;
text-align: center;
background-color: #ffffff;
border-radius: 16px;
border: 1px dashed #cbd5e1;
color: #64748b;
font-size: 15px;
}
.cards-grid {
display: grid;
grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
gap: 16px;
}
.admin-card {
background-color: #ffffff;
border: 1.5px solid #e2e8f0;
border-radius: 16px;
padding: 18px;
display: flex;
flex-direction: column;
gap: 12px;
}
.admin-card.is-pending {
border-color: #f59e0b;
background-color: #fffbeb;
}
.card-header {
display: flex;
justify-content: space-between;
align-items: flex-start;
gap: 10px;
}
.company-title {
display: block;
font-size: 16px;
font-weight: 800;
}
.unp-tag {
font-size: 12px;
font-weight: 700;
color: #0284c7;
}
.status-pill {
font-size: 11px;
font-weight: 700;
padding: 4px 9px;
border-radius: 999px;
white-space: nowrap;
display: inline-flex; 
align-items: center; 
justify-content: center; 
gap: 5px;
}
.status-pill.pending {
background-color: #fef3c7;
color: #92400e;
}
.status-pill.approved {
background-color: #dcfce7;
color: #166534;
}
.status-pill.rejected {
background-color: #fee2e2;
color: #b91c1c;
}
.card-details {
font-size: 13px;
color: #334155;
display: flex;
flex-direction: column;
gap: 4px;
}
.card-actions {
display: flex;
gap: 8px;
margin-top: auto;
padding-top: 8px;
}
.btn-approve,
.btn-reject {
flex: 1;
height: 38px;
border-radius: 10px;
border: none;
font-size: 13px;
font-weight: 700;
cursor: pointer;
display: inline-flex; 
align-items: center; 
justify-content: center; 
gap: 5px;
}
.btn-approve {
background-color: #16a34a;
color: #ffffff;
}
.btn-reject {
background-color: #fee2e2;
color: #b91c1c;
}
/* Заказы */
.orders-admin-list {
display: flex;
flex-direction: column;
gap: 14px;
}
.order-admin-card {
background-color: #ffffff;
border: 1px solid #cbd5e1;
border-radius: 16px;
padding: 18px;
display: flex;
flex-direction: column;
gap: 12px;
}
.order-admin-head {
display: flex;
flex-wrap: wrap;
justify-content: space-between;
align-items: center;
gap: 10px;
padding-bottom: 10px;
border-bottom: 1px solid #e2e8f0;
}
.order-num {
font-size: 16px;
font-weight: 800;
margin-right: 8px;
}
.order-date {
font-size: 12px;
color: #64748b;
margin-right: 8px;
}
.role-badge {
font-size: 11px;
font-weight: 700;
padding: 3px 8px;
border-radius: 8px;
background-color: #f1f5f9;
}
.role-badge.wholesale {
background-color: #0f172a;
color: #A3D2F9;
}
.order-sum {
font-size: 18px;
font-weight: 800;
}
.order-client-info {
font-size: 13px;
color: #334155;
display: flex;
flex-direction: column;
gap: 4px;
}
.order-items-mini {
list-style: none;
background-color: #f8fafc;
padding: 10px 12px;
border-radius: 10px;
font-size: 13px;
display: flex;
flex-direction: column;
gap: 4px;
}
.order-controls {
display: flex;
flex-wrap: wrap;
align-items: flex-end;
gap: 12px;
padding-top: 8px;
border-top: 1px dashed #cbd5e1;
}
.control-group {
display: flex;
flex-direction: column;
gap: 4px;
min-width: 220px;
}
.control-group label {
font-size: 11px;
font-weight: 700;
color: #475569;
}
.admin-select,
.admin-input {
height: 38px;
padding: 0 10px;
border-radius: 9px;
border: 1.5px solid #cbd5e1;
font-size: 13px;
background-color: #ffffff;
}
.btn-save-order {
height: 38px;
padding: 0 18px;
border-radius: 9px;
border: none;
background-color: #0f172a;
color: #A3D2F9;
font-size: 13px;
font-weight: 700;
cursor: pointer;
}

/* Товары и остатки */
.products-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.admin-search-input {
  flex: 1;
  min-width: 240px;
  height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  font-size: 14px;
}

.btn-add-product {
  height: 40px;
  padding: 0 18px;
  border-radius: 10px;
  border: none;
  background-color: #16a34a;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
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
}

.sub-text {
  font-size: 11px;
  color: #64748b;
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

.row-actions {
  display: flex;
  gap: 6px;
}

.btn-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.16s ease;
}

.btn-icon.save {
  background-color: #f0fdf4;
  border-color: #86efac;
  color: #16a34a;
}

.btn-icon.save:hover {
  background-color: #16a34a;
  border-color: #16a34a;
  color: #ffffff;
}

.btn-icon.edit {
  background-color: #f0f9ff;
  border-color: #7dd3fc;
  color: #0284c7;
}

.btn-icon.edit:hover {
  background-color: #0284c7;
  border-color: #0284c7;
  color: #ffffff;
}

.btn-icon.del {
  background-color: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-icon.del:hover {
  background-color: #dc2626;
  border-color: #dc2626;
  color: #ffffff;
}


/* Модальное окно редактора товара */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 400;
}

.product-editor-modal {
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  background-color: #ffffff;
  border-radius: 18px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #0f172a;
  color: #ffffff;
}

.close-editor {
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 18px;
  cursor: pointer;
}

.editor-body {
  padding: 18px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.f-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.f-group label {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}

.f-group input,
.f-group select,
.f-group textarea {
  width: 100%;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 9px;
  border: 1.5px solid #cbd5e1;
  font-size: 13px;
}

.attrs-editor {
  background-color: #f8fafc;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attrs-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
}

.btn-add-attr {
  padding: 4px 10px;
  border-radius: 7px;
  border: 1px solid #0284c7;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.attr-row {
  display: grid;
  grid-template-columns: 1fr 1.3fr 32px;
  gap: 8px;
}

.attr-row input {
  height: 34px;
  padding: 0 8px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 13px;
}

.btn-del-attr {
  border: none;
  background-color: #fee2e2;
  color: #b91c1c;
  border-radius: 8px;
  cursor: pointer;
}

.editor-foot {
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel {
  height: 38px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  cursor: pointer;
}

.btn-submit-prod {
  height: 38px;
  padding: 0 18px;
  border-radius: 10px;
  border: none;
  background-color: #16a34a;
  color: #ffffff;
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 640px) {
  .form-grid-2,
  .form-grid-4 {
    grid-template-columns: 1fr;
  }
}

.upload-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.upload-row input[type="text"] {
  flex: 1;
}

.btn-upload-file {
  height: 36px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1.5px solid #0284c7;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  white-space: nowrap;
}

.editor-img-preview {
  width: 72px;
  height: 72px;
  object-fit: contain;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  margin-top: 6px;
  background-color: #f8fafc;
}

/* Панель фильтрации заказов по статусам */
.order-filters-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-pill-btn {
  height: 36px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  transition: all 0.15s ease;
}

.filter-pill-btn:hover {
  border-color: #0f172a;
  color: #0f172a;
}

.filter-pill-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
}

.filter-pill-count {
  background-color: #f1f5f9;
  color: #475569;
  font-size: 11px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
}

.filter-pill-btn.active .filter-pill-count {
  background-color: #A3D2F9;
  color: #0f172a;
}

.order-top-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  align-items: center;
}

.order-search-wrap {
  position: relative;
  flex: 1;
  min-width: 260px;
  display: flex;
  align-items: center;
}

.order-search-wrap .admin-search-input {
  width: 100%;
  padding-right: 34px;
}

.btn-clear-order-search {
  position: absolute;
  right: 8px;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background-color: #e2e8f0;
  color: #475569;
  font-size: 12px;
  cursor: pointer;
}

.role-segment-group {
  display: inline-flex;
  background-color: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  padding: 3px;
  gap: 3px;
}

.role-seg-btn {
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.role-seg-btn.active {
  background-color: #0f172a;
  color: #A3D2F9;
}

.btn-reset-orders {
  margin-top: 10px;
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 9px;
  background-color: #0f172a;
  color: #A3D2F9;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

/* Навигация в шапке админки */
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
  align-items: 
  center; gap: 6px;
}

.btn-back-menu:hover {
  background-color: #A3D2F9;
  color: #0f172a;
}

/* ГЛАВНОЕ МЕНЮ АДМИНКИ (ХАБ) */
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

/* Сетка карточек разделов */
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
  font-size: 24px;
}

.hub-icon-box.gold {
  background-color: #fef3c7;
}

.hub-icon-box.blue {
  background-color: #e0f2fe;
}

.hub-icon-box.emerald {
  background-color: #dcfce7;
}

.hub-icon-box.purple {
  background-color: #f3e8ff;
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

/* Карточка-задел на будущее */
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

.future-icon {
  font-size: 28px;
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

.icon-picker-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.icon-pick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 6px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #334155;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.icon-pick-btn:hover {
  border-color: #0f172a;
}

.icon-pick-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
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


</style>