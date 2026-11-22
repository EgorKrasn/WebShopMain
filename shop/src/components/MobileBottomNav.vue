<script setup>
import { useRoute } from 'vue-router'
import { Home, Watch, ShoppingCart, User } from 'lucide-vue-next'

const props = defineProps({
  cartCount: {
    type: Number,
    default: 0
  },
  currentUser: {
    type: Object,
    default: null
  },
  isCartOpen: {
    type: Boolean,
    default: false
  },
  isAccountOpen: {
    type: Boolean,
    default: false
  },
  isAuthOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['go-home', 'go-catalog', 'open-cart', 'open-account', 'open-auth'])

const route = useRoute()

const handleAccountTap = () => {
  if (props.currentUser) {
    emit('open-account')
  } else {
    emit('open-auth', 'login')
  }
}
</script>

<template>
  <nav class="mobile-bottom-nav" aria-label="Нижняя мобильная навигация">
    <button
      type="button"
      class="bottom-nav-item"
      :class="{ active: !isCartOpen && !isAccountOpen && !isAuthOpen && route.name === 'home' }"
      @click="emit('go-home')"
    >
      <Home :size="20" :stroke-width="2.1" />
      <span>Главная</span>
    </button>

    <button
      type="button"
      class="bottom-nav-item"
      :class="{
        active:
          !isCartOpen &&
          !isAccountOpen &&
          !isAuthOpen &&
          (route.name === 'catalog' || route.name === 'product')
      }"
      @click="emit('go-catalog')"
    >
      <Watch :size="20" :stroke-width="2.1" />
      <span>Каталог</span>
    </button>

    <button
      type="button"
      class="bottom-nav-item"
      :class="{ active: isCartOpen }"
      @click="emit('open-cart')"
    >
      <span class="icon-badge-wrap">
        <ShoppingCart :size="20" :stroke-width="2.1" />
        <span v-if="cartCount > 0" class="bottom-cart-badge">
          {{ cartCount > 99 ? '99+' : cartCount }}
        </span>
      </span>
      <span>Корзина</span>
    </button>

    <button
      type="button"
      class="bottom-nav-item"
      :class="{ active: isAccountOpen || isAuthOpen }"
      @click="handleAccountTap"
    >
      <span class="icon-badge-wrap">
        <User :size="20" :stroke-width="2.1" />
        <span v-if="currentUser" class="user-online-dot"></span>
      </span>
      <span>{{ currentUser ? 'Кабинет' : 'Войти' }}</span>
    </button>
  </nav>
</template>

<style scoped>
.mobile-bottom-nav {
  display: none;
}

@media (max-width: 960px) {
  .mobile-bottom-nav {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 120;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    background-color: rgba(15, 23, 42, 0.96);
    backdrop-filter: blur(10px);
    border-top: 1px solid rgba(163, 210, 249, 0.25);
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom, 0px));
    box-shadow: 0 -6px 20px rgba(15, 23, 42, 0.28);
  }

  .bottom-nav-item {
    border: none;
    background: transparent;
    color: #94a3b8;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    padding: 5px 4px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    transition: color 0.16s ease, background-color 0.16s ease;
    -webkit-tap-highlight-color: transparent;
  }

  .bottom-nav-item:hover {
    color: #e2e8f0;
  }

  .bottom-nav-item.active {
    color: #A3D2F9;
    background-color: rgba(163, 210, 249, 0.12);
  }

  .icon-badge-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .bottom-cart-badge {
    position: absolute;
    top: -5px;
    right: -11px;
    min-width: 17px;
    height: 17px;
    padding: 0 4px;
    border-radius: 999px;
    background-color: #f59e0b;
    color: #0f172a;
    font-size: 10px;
    font-weight: 900;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }

  .user-online-dot {
    position: absolute;
    top: -1px;
    right: -3px;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #22c55e;
    border: 1.5px solid #0f172a;
  }
}
</style>
