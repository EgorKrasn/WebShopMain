<script setup>
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { api } from './services/api.js'
import Navbar from './components/Navbar.vue'
import ProductCatalog from './components/ProductCatalog.vue'
import ProductModal from './components/ProductModal.vue'
import AuthModal from './components/AuthModal.vue'
import CartDrawer from './components/CartDrawer.vue'
import AccountModal from './components/AccountModal.vue'
import Footer from './components/Footer.vue'
import AdminPanel from './components/AdminPanel.vue'
import HomeView from './views/HomeView.vue'
import CategorySidebar from './components/CategorySidebar.vue'
import { ArrowLeft, Settings, CheckCircle2 } from 'lucide-vue-next'
import { useBackdropClose } from './composables/useBackdropClose.js'




const isAuthModalOpen = ref(false)
const authModalMode = ref('login')
const isCartOpen = ref(false)
const isAccountOpen = ref(false)
const cartItems = ref([])
const selectedProduct = ref(null)
const orderSuccessInfo = ref(null)

const currentUser = ref(null)
const userOrders = ref([])

const pendingCartAction = ref(null)

const route = useRoute()
const router = useRouter()

const successBackdrop = useBackdropClose(() => { orderSuccessInfo.value = null })



const userRole = computed(() => {
  return currentUser.value?.role || 'retail'
})

const searchQuery = ref('')
const selectedCategory = ref('')
const selectedSubcategory = ref('')

const handleSelectCategory = (payload) => {
  if (typeof payload === 'string') {
    selectedCategory.value = payload
    selectedSubcategory.value = ''
  } else if (payload && typeof payload === 'object') {
    selectedCategory.value = payload.category || ''
    selectedSubcategory.value = payload.subcategory || ''
  }
  if (route.name !== 'catalog') {
    router.push({ name: 'catalog' })
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}


const loadUserOrders = async () => {
  const token = localStorage.getItem('sandrintime_token')
  if (!token || !currentUser.value) {
    userOrders.value = []
    return
  }
  try {
    userOrders.value = await api.getOrders()
  } catch (err) {
    console.error('Ошибка загрузки заявок:', err)
    if (err.message.includes('Сессия истекла')) {
      handleLogout()
    }
  }
}


const totalCartCount = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
})

const openAuth = (mode = 'login') => {
  authModalMode.value = mode
  isAuthModalOpen.value = true
}

const handleAuthSuccess = async (result) => {
  const updatedUser = result?.user || result
  if (!updatedUser) return

  currentUser.value = {
    id: updatedUser.id,
    role: updatedUser.role,
    wholesaleStatus: updatedUser.wholesaleStatus || null,
    email: updatedUser.email,
    name: updatedUser.name,
    companyName: updatedUser.companyName || null,
    contactName: updatedUser.contactName,
    unp: updatedUser.unp
  }

  localStorage.setItem('sandrintime_user', JSON.stringify(currentUser.value))

  if (result?.access_token) {
    localStorage.setItem('sandrintime_token', result.access_token)
  } else if (result?.token) {
    localStorage.setItem('sandrintime_token', result.token)
  }

  await loadUserOrders()

  if (pendingCartAction.value) {
    const { product, quantity } = pendingCartAction.value
    pendingCartAction.value = null
    addProductWithQuantity(product, quantity)
  }
}


watch(
  () => currentUser.value?.role,
  (newRole) => {
    if (newRole) {
      
      localStorage.setItem('sandrintime_role', newRole)
    } else {
      
      localStorage.setItem('sandrintime_role', 'retail')
    }
  }
)


const handleLogout = () => {
  currentUser.value = null
  userOrders.value = []
  localStorage.removeItem('sandrintime_user')
  localStorage.removeItem('sandrintime_token')
  localStorage.removeItem('sandrintime_cart')
}

const openAccountModal = async () => {
  isAccountOpen.value = true
  await loadUserOrders()
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  selectedSubcategory.value = ''
}


const handleAddToCart = (product) => {
  addProductWithQuantity(product, 1)
}

const handleAddFromModal = ({ product, quantity }) => {
  addProductWithQuantity(product, quantity)
}

const addProductWithQuantity = (product, qtyToAdd) => {
  if (!currentUser.value) {
    pendingCartAction.value = { product, quantity: qtyToAdd }
    openAuth('login')
    return
  }

  const existing = cartItems.value.find((item) => item.id === product.id)
  if (existing) {
    existing.quantity += qtyToAdd
  } else {
    cartItems.value.push({
      id: product.id,
      sku: product.sku,
      name: product.name,
      icon: product.icon,
      image: product.image || null,
      retailPrice: product.retailPrice,
      wholesalePrice: product.wholesalePrice,
      minWholesaleQty: product.minWholesaleQty || 1,
      quantity: qtyToAdd
    })
  }
}



const handleRepeatOrder = (itemsToRepeat) => {
  itemsToRepeat.forEach((item) => {
    const existing = cartItems.value.find((c) => c.id === item.product_id)
    if (existing) {
      existing.quantity += item.quantity
    } else {
      cartItems.value.push({
        id: item.product_id,
        sku: item.sku,
        name: item.name,
        icon: '⌚',
        image: null,
        retailPrice: item.unit_price,
        wholesalePrice: item.unit_price,
        quantity: item.quantity
      })
    }
  })
  isCartOpen.value = true
}

const handleUpdateQty = ({ id, delta }) => {
  const item = cartItems.value.find((i) => i.id === id)
  if (!item) return

  item.quantity += delta
  if (item.quantity <= 0) {
    handleRemoveItem(id)
  }
}

const handleSetQty = ({ id, quantity }) => {
  if (quantity <= 0) {
    handleRemoveItem(id)
    return
  }
  const target = cartItems.value.find((item) => item.id === id)
  if (target) {
    target.quantity = quantity
  }
}

const handleRemoveItem = (id) => {
  cartItems.value = cartItems.value.filter((i) => i.id !== id)
}

const handleClearCart = () => {
  cartItems.value = []
}


const handleCheckout = async (orderPayload) => {
  const isEuropost = orderPayload.delivery?.method === 'europost'

  try {
    const createdOrder = await api.createOrder(orderPayload)

    if (currentUser.value) {
      await loadUserOrders()
    }

    orderSuccessInfo.value = {
      isEuropost,
      title: `Заявка №${createdOrder.number} оформлена!`,
      message: isEuropost
        ? 'Заявка отправлена в обработку для уточнения цены доставки.'
        : 'Заявка отправлена в обработку.',
      subtext: isEuropost
        ? 'Вы можете отслеживать статус заявки в личном кабинете. Менеджер свяжется с вами после расчёта стоимости доставки Европочтой.'
        : 'Вы можете отслеживать статус заявки в личном кабинете. Ожидайте звонка менеджера.'
    }

    cartItems.value = []
    isCartOpen.value = false
  } catch (err) {
    alert(`Не удалось отправить заявку на сервер: ${err.message}`)
  }
}

const allProducts = ref([])


// 1. Открытие карточки товара (меняет URL на /product/ST-1111)
const openProductModal = (product) => {
  if (!product) return
  selectedProduct.value = product
  if (route.params.sku !== product.sku) {
    router.push({ name: 'product', params: { sku: product.sku } })
  }
}

// 2. Закрытие карточки товара (возвращает URL на /)
const closeProductModal = () => {
  selectedProduct.value = null
  if (route.name === 'product') {
    router.push({ name: 'catalog' })
  }
}


// 3. Переключение цвета внутри модального окна (обновляет URL на артикул нового цвета)
const handleSelectVariant = (variantId) => {
  const target = allProducts.value.find((item) => item.id === variantId)
  if (target) {
    openProductModal(target)
  }
}

// 4. Автоматическое открытие карточки, если зашли по прямой ссылке /product/ST-1111
// или нажали кнопку «Назад / Вперёд» в браузере
watch(
  [() => route.params.sku, allProducts],
  ([sku, productsList]) => {
    if (!sku) {
      selectedProduct.value = null
      return
    }
    if (Array.isArray(productsList) && productsList.length > 0) {
      const found = productsList.find(
        (p) => p.sku.toLowerCase() === String(sku).toLowerCase()
      )
      selectedProduct.value = found || null
    }
  },
  { immediate: true }
)

const loadProducts = async () => {
  try {
    const serverProducts = await api.getProducts()
    if (Array.isArray(serverProducts)) {
      allProducts.value = serverProducts
    }
  } catch (err) {
    console.warn('Не удалось загрузить товары:', err.message)
  }
}

onMounted(async () => {
  // 0. Загружаем категории и товары параллельно
  await Promise.all([loadCategories(), loadProducts()])

  // 1. Восстанавливаем корзину из localStorage
  const savedCart = localStorage.getItem('sandrintime_cart')
  if (savedCart) {
    try {
      const parsedCart = JSON.parse(savedCart)
      if (Array.isArray(parsedCart)) {
        cartItems.value = parsedCart
      }
    } catch {
      localStorage.removeItem('sandrintime_cart')
    }
  }

  // 2. Восстанавливаем пользователя
  const savedUser = localStorage.getItem('sandrintime_user')
  if (savedUser) {
    try {
      currentUser.value = JSON.parse(savedUser)
      await loadUserOrders()
    } catch {
      localStorage.removeItem('sandrintime_user')
    }
  }
})


watch(
  cartItems,
  (newCart) => {
    localStorage.setItem('sandrintime_cart', JSON.stringify(newCart))
  },
  { deep: true }
)

const isAdmin = computed(() => currentUser.value?.role === 'admin')
const isAdminPage = computed(() => route.name === 'admin')

const openAdminPanel = () => {
  if (isAdmin.value) {
    router.push({ name: 'admin' })
  }
}

const closeAdminPanel = () => {
  router.push({ name: 'home' })
}
watch([isAdminPage, currentUser], ([inAdmin]) => { if (inAdmin && !isAdmin.value) router.replace({ name: 'home' }) }, { immediate: true })

const categories = ref([])

const loadCategories = async () => {
  try {
    const data = await api.getCategories()
    if (Array.isArray(data)) {
      categories.value = data
    }
  } catch (err) {
    console.warn('Не удалось загрузить категории:', err.message)
  }
}


const goToHome = () => {
  resetFilters()
  router.push({ name: 'home' })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const goToCatalog = () => {
  router.push({ name: 'catalog' })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Если пользователь начал вводить поиск с главной страницы — автоматически открываем каталог
watch(searchQuery, (newVal) => {
  if (newVal.trim() && route.name === 'home') {
    router.push({ name: 'catalog' })
  }
})


</script>




<template>
  <div class="app-layout">

    <button
      v-if="isAdmin"
      type="button"
      class="btn-admin-nav"
      style="display: inline-flex; align-items: center; gap: 6px;"
      @click="isAdminPage ? closeAdminPanel() : openAdminPanel()"
    >
      <template v-if="isAdminPage">
        <ArrowLeft :size="15" />
        <span>Вернуться в магазин</span>
      </template>
      <template v-else>
        <Settings :size="15" />
        <span>Админ-панель</span>
      </template>
    </button>


    <Navbar 
      :key="'nav-' + (currentUser?.role || 'guest')"
      :cart-count="totalCartCount"
      :current-user="currentUser"
      :categories="categories"
      @open-auth="openAuth" 
      @open-account="openAccountModal"
      @logout="handleLogout"
      @open-cart="isCartOpen = true"
      @update-search="searchQuery = $event"
      @select-category="handleSelectCategory"
      @go-home="goToHome"
      @go-catalog="goToCatalog"
    />



    <AuthModal 
      :is-open="isAuthModalOpen" 
      :initial-mode="authModalMode"
      @close="isAuthModalOpen = false; pendingCartAction = null"
      @success="handleAuthSuccess"
    />
    
    <main class="main-content">
      <AdminPanel
        v-if="isAdminPage && isAdmin"
        @close="closeAdminPanel"
        @categories-updated="loadCategories"
      />

      <div v-else class="shop-shell">
        <CategorySidebar
          v-if="route.name !== 'home'"
          :categories="categories"
          :selected-category="selectedCategory"
          :selected-subcategory="selectedSubcategory"
          @select-category="handleSelectCategory"
        />

        <div class="shop-content-area">
          <HomeView
            v-if="route.name === 'home'"
            :categories="categories"
            :products="allProducts"
            :current-user="currentUser"
            @go-catalog="goToCatalog"
            @select-category="handleSelectCategory"
            @open-auth="openAuth"
            @open-account="openAccountModal"
            @select-product="openProductModal"
          />

          <ProductCatalog 
            v-else
            :products="allProducts"
            :user-role="userRole"
            :cart-items="cartItems"
            :search-query="searchQuery"
            :selected-category="selectedCategory"
            :selected-subcategory="selectedSubcategory"
            @update-search="searchQuery = $event"
            @select-product="openProductModal"
            @add-to-cart="handleAddToCart"
            @update-qty="handleUpdateQty"
            @set-qty="handleSetQty"
            @reset-filters="resetFilters"
          />

        </div>
      </div>
    </main>



    <!-- Модальное окно подробного просмотра товара -->
    <ProductModal
      :product="selectedProduct"
      :user-role="userRole"
      :cart-items="cartItems"
      @select-variant="handleSelectVariant"
      @close="closeProductModal"
      @add-to-cart="handleAddFromModal"
    />

    <AccountModal
      :is-open="isAccountOpen"
      :current-user="currentUser"
      :orders="userOrders"
      @close="isAccountOpen = false"
      @logout="handleLogout"
      @repeat-order="handleRepeatOrder"
      @user-updated="handleAuthSuccess"
    />

    <CartDrawer 
      :is-open="isCartOpen"
      :items="cartItems"
      :user-role="userRole"
      :current-user="currentUser"
      @close="isCartOpen = false"
      @update-qty="handleUpdateQty"
      @set-qty="handleSetQty"
      @remove-item="handleRemoveItem"
      @clear-cart="handleClearCart"
      @checkout="handleCheckout"
    />

      <Footer 
      @select-category="handleSelectCategory"
      @open-auth="openAuth"
      @open-cart="isCartOpen = true"
    />

        <!-- Всплывающее окно об успешной отправке заявки -->
    <Transition name="fade">
      <div
        v-if="orderSuccessInfo"
        class="success-backdrop"
        @mousedown.self="successBackdrop.onBackdropMouseDown"
        @mouseup.self="successBackdrop.onBackdropMouseUp"
      >
        <div class="success-modal" role="dialog" aria-modal="true">
          <div class="success-icon">
            <CheckCircle2 :size="48" color="#16a34a" :stroke-width="2" />
          </div>

          <h3 class="success-title">{{ orderSuccessInfo.title }}</h3>
          <p class="success-main-msg">{{ orderSuccessInfo.message }}</p>
          <p class="success-sub-msg">{{ orderSuccessInfo.subtext }}</p>
          <button type="button" class="btn-success-ok" @click="orderSuccessInfo = null">
            Понятно
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>




<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html,
body,
#app {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
  overflow-x: clip;
}


body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: linear-gradient(135deg, #A3D2F9 0%, #D4EAFC 50%, #89C2F5 100%);
  background-attachment: fixed;
  color: #0f172a;
  line-height: 1.5;
}

.app-layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
   padding-top: 28px;
}

/* Всплывающее окно после отправки заявки */
.success-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 400;
}

.success-modal {
  width: 100%;
  max-width: 420px;
  background-color: #ffffff;
  border-radius: 20px;
  padding: 28px 24px 24px;
  text-align: center;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.success-icon {
  font-size: 46px;
  margin-bottom: 4px;
}

.success-title {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.success-main-msg {
  font-size: 15px;
  font-weight: 700;
  color: #0284c7;
  line-height: 1.4;
}

.success-sub-msg {
  font-size: 13px;
  color: #475569;
  line-height: 1.45;
}

.btn-success-ok {
  margin-top: 8px;
  height: 44px;
  width: 100%;
  border: none;
  border-radius: 12px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-success-ok:hover {
  background-color: #7cc0f8;
}

.main-content {
  flex: 1;
  width: 100%;
  padding-top: 28px;
  padding-bottom: 48px;
}

.btn-admin-nav {
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #f59e0b;
  background-color: #fef3c7;
  color: #92400e;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-admin-nav:hover {
  background-color: #f59e0b;
  color: #ffffff;
}

.shop-shell {
  max-width: 1520px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: flex-start;
  gap: 24px;
}

.shop-content-area {
  flex: 1;
  min-width: 0;
}

/* Убираем лишние боковые поля у внутренних страниц на ПК, т.к. их задаёт .shop-shell */
@media (min-width: 961px) {
  .shop-content-area .home-page,
  .shop-content-area .catalog-section {
    padding-left: 0;
    padding-right: 0;
    padding-top: 0;
  }
}

@media (max-width: 960px) {
  .shop-shell {
    padding: 0;
    display: block;
  }
}


</style>
