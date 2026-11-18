<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from './services/api.js'
import Navbar from './components/Navbar.vue'
import ProductCatalog from './components/ProductCatalog.vue'
import ProductModal from './components/ProductModal.vue'
import AuthModal from './components/AuthModal.vue'
import CartDrawer from './components/CartDrawer.vue'
import AccountModal from './components/AccountModal.vue'
import Footer from './components/Footer.vue'

const isAuthModalOpen = ref(false)
const authModalMode = ref('login')
const isCartOpen = ref(false)
const isAccountOpen = ref(false)
const cartItems = ref([])
const selectedProduct = ref(null)
const orderSuccessInfo = ref(null)

const currentUser = ref(null)
const userOrders = ref([])

const userRole = computed(() => {
  return currentUser.value?.role || 'retail'
})

const searchQuery = ref('')
const selectedCategory = ref('')

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

onMounted(async () => {
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
    email: updatedUser.email,
    name: updatedUser.name,
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
}

const handleLogout = () => {
  currentUser.value = null
  userOrders.value = []
  localStorage.removeItem('sandrintime_user')
  localStorage.removeItem('sandrintime_token')
}

const openAccountModal = async () => {
  isAccountOpen.value = true
  await loadUserOrders()
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
}

const handleAddToCart = (product) => {
  addProductWithQuantity(product, 1)
}

const handleAddFromModal = ({ product, quantity }) => {
  addProductWithQuantity(product, quantity)
}

const addProductWithQuantity = (product, qtyToAdd) => {
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

const handleRemoveItem = (id) => {
  cartItems.value = cartItems.value.filter((i) => i.id !== id)
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
</script>

<template>
  <div class="app-layout">
    <Navbar 
      :key="'nav-' + (currentUser?.role || 'guest')"
      :cart-count="totalCartCount"
      :current-user="currentUser"
      @open-auth="openAuth" 
      @open-account="openAccountModal"
      @logout="handleLogout"
      @open-cart="isCartOpen = true"
      @update-search="searchQuery = $event"
      @select-category="selectedCategory = $event"
    />

    <main class="main-content">
      <ProductCatalog 
        :user-role="userRole" 
        :cart-items="cartItems"
        :search-query="searchQuery"
        :selected-category="selectedCategory"
        @add-to-cart="handleAddToCart"
        @reset-filters="resetFilters"
        @select-product="selectedProduct = $event"
      />
    </main>

    <ProductModal
      :product="selectedProduct"
      :user-role="userRole"
      :cart-items="cartItems"
      @close="selectedProduct = null"
      @add-to-cart="handleAddFromModal"
    />

    <AuthModal 
      :is-open="isAuthModalOpen" 
      :initial-mode="authModalMode"
      @close="isAuthModalOpen = false"
      @success="handleAuthSuccess"
    />

    <CartDrawer 
      :is-open="isCartOpen"
      :items="cartItems"
      :user-role="userRole"
      :current-user="currentUser"
      @close="isCartOpen = false"
      @update-qty="handleUpdateQty"
      @remove-item="handleRemoveItem"
      @checkout="handleCheckout"
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

    <Transition name="fade">
      <div v-if="orderSuccessInfo" class="success-backdrop" @click.self="orderSuccessInfo = null">
        <div class="success-modal" role="dialog" aria-modal="true">
          <div class="success-icon">✅</div>
          <h3 class="success-title">{{ orderSuccessInfo.title }}</h3>
          <p class="success-main-msg">{{ orderSuccessInfo.message }}</p>
          <p class="success-sub-msg">{{ orderSuccessInfo.subtext }}</p>
          <button type="button" class="btn-success-ok" @click="orderSuccessInfo = null">
            Понятно
          </button>
        </div>
      </div>
    </Transition>

    <Footer 
      @select-category="selectedCategory = $event"
      @open-auth="openAuth"
      @open-cart="isCartOpen = true"
    />
  </div>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: #D4EAFC;
  color: #0f172a;
  line-height: 1.5;
  overflow-x: hidden;
}

.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  padding-top: 28px;
  padding-bottom: 48px;
}

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

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.22s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
