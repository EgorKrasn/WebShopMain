<script setup>
import { ref } from 'vue'

const props = defineProps({
  cartCount: {
    type: Number,
    default: 0
  },
  currentUser: {
    type: Object,
    default: null
  },
  categories: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'open-auth',
  'logout',
  'open-cart',
  'update-search',
  'select-category',
  'open-account',
  'go-home',
  'go-catalog'
])



// Состояние выдвижного меню каталога слева
const isCatalogOpen = ref(false)

// Активная категория в левом меню
const activeCategory = ref(0)

// Поисковый запрос
const searchQuery = ref('')




const toggleCatalog = () => {
  isCatalogOpen.value = !isCatalogOpen.value
}

const closeCatalog = () => {
  isCatalogOpen.value = false
}

const onSearchInput = () => {
  emit('update-search', searchQuery.value)
}

const handleSearch = () => {
  emit('update-search', searchQuery.value)
}

const clearSearch = () => {
  searchQuery.value = ''
  emit('update-search', '')
}

const selectCategory = (categoryName, subcategoryName = '') => {
  emit('select-category', {
    category: categoryName,
    subcategory: subcategoryName
  })
  closeCatalog()
}

</script>

<template>
  <header class="header">
    <div class="container header-inner">
      
      <!-- 1. Логотип (возвращает на приветственную страницу) -->
      <a href="/" class="logo-slot" @click.prevent="clearSearch(); closeCatalog(); emit('go-home')">
        <div class="logo-placeholder">LOGO</div>
        <span class="brand-name">Сандрин<span class="brand-accent">Тайм</span></span>
      </a>


      <!-- Навигация по центру шапки для ПК -->
      <nav class="desktop-nav" aria-label="Основная навигация">
        <button
          type="button"
          class="nav-pill"
          :class="{ active: $route.name === 'home' }"
          @click="clearSearch(); emit('go-home')"
        >
          🏠 Главная
        </button>

        <button
          type="button"
          class="nav-pill"
          :class="{ active: $route.name === 'catalog' || $route.name === 'product' }"
          @click="emit('go-catalog')"
        >
          ⌚ Каталог
        </button>

        <button
          v-if="!currentUser"
          type="button"
          class="nav-pill"
          @click="emit('open-auth', 'register')"
        >
          🏢 Опт / Юрлицам
        </button>

        <button
          v-else
          type="button"
          class="nav-pill"
          @click="emit('open-account')"
        >
          📋 Мои заявки
        </button>
      </nav>



      <!-- 2. Общий блок: Кнопка категорий вплотную слева от поиска -->
      <div class="search-group">
        <button 
          type="button" 
          class="wb-catalog-btn" 
          :class="{ 'is-active': isCatalogOpen }"
          @click="toggleCatalog"
          aria-label="Открыть каталог товаров"
        >
          <svg v-if="!isCatalogOpen" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
            <line x1="4" y1="6" x2="20" y2="6"></line>
            <line x1="4" y1="12" x2="20" y2="12"></line>
            <line x1="4" y1="18" x2="20" y2="18"></line>
          </svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        <form class="search-bar" @submit.prevent="handleSearch">
          <input 
            v-model="searchQuery" 
            @input="onSearchInput"
            type="text" 
            class="search-input" 
            placeholder="Найти часы, бренд или артикул..."
          />
          <button 
            v-if="searchQuery" 
            type="button" 
            class="search-clear" 
            @click="clearSearch"
            aria-label="Очистить поиск"
          >
            ✕
          </button>
          <button type="submit" class="search-submit" aria-label="Найти">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
          </button>
        </form>
      </div>

      <!-- 3. Правая часть: Профиль пользователя (или кнопка Вход) + Корзина -->
      <div class="header-actions">
        <div class="auth-buttons">
          <div v-if="currentUser" class="user-profile-pill">
            <div class="user-clickable-area" @click="emit('open-account')" title="Открыть личный кабинет">
              <div class="user-avatar" :class="{ wholesale: currentUser.role === 'wholesale' }">
                {{ currentUser.role === 'wholesale' ? '🏢' : '👤' }}
              </div>
              <div class="user-meta">
                <span class="user-name">{{ currentUser.name }}</span>
                <span v-if="currentUser.role === 'wholesale'" class="user-badge wholesale">
                  УНП {{ currentUser.unp }}
                </span>
                <span v-else class="user-badge">Мои заявки</span>
              </div>
            </div>
            <button 
              type="button" 
              class="btn-logout" 
              @click="emit('logout')" 
              title="Выйти из аккаунта"
            >
              Выйти
            </button>
          </div>


          <button v-else type="button" class="btn-login" @click="emit('open-auth', 'login')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Войти</span>
          </button>
        </div>

        <button 
          type="button" 
          class="btn-cart" 
          aria-label="Корзина" 
          @click="closeCatalog(); emit('open-cart')"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="9" cy="21" r="1"></circle>
            <circle cx="20" cy="21" r="1"></circle>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
          </svg>
          <span class="cart-text">Корзина</span>
          <span v-if="cartCount > 0" class="cart-badge">{{ cartCount }}</span>
        </button>
      </div>

    </div>
  </header>

  <!-- Затемнение фона при открытом каталоге -->
  <Transition name="fade">
    <div v-if="isCatalogOpen" class="drawer-backdrop" @click="closeCatalog"></div>
  </Transition>

  <!-- Выезжающая слева панель категорий -->
  <Transition name="slide-left">
    <aside v-if="isCatalogOpen" class="catalog-drawer">
      <div class="drawer-header">
        <h2 class="drawer-title">Каталог товаров</h2>
        <button type="button" class="drawer-close" @click="closeCatalog">✕</button>
      </div>

      <div class="drawer-body">
        <ul class="category-list">
          <li class="category-item" @click="selectCategory('')">
            <span class="cat-icon">📋</span>
            <span class="cat-name">Все товары каталога</span>
            <span class="cat-arrow">›</span>
          </li>

          <li 
            v-for="(cat, index) in categories" 
            :key="cat.id"
            class="category-item"
            :class="{ active: activeCategory === index }"
            @mouseenter="activeCategory = index"
            @click="selectCategory(cat.name)"
          >
            <span class="cat-icon">{{ cat.icon }}</span>
            <span class="cat-name">{{ cat.name }}</span>
            <span class="cat-arrow">›</span>
          </li>
        </ul>

        <div class="subcategory-panel" v-if="categories[activeCategory]">
          <h3 class="subcat-title">{{ categories[activeCategory].name }}</h3>
          <ul class="subcat-list">
            <li>
              <a
                href="#catalog"
                class="subcat-link all-cat-link"
                @click.prevent="selectCategory(categories[activeCategory].name, '')"
              >
                Смотреть все в разделе «{{ categories[activeCategory].name }}» →
              </a>
            </li>
            <li v-for="sub in categories[activeCategory].subcategories" :key="sub">
              <a
                href="#catalog"
                class="subcat-link"
                @click.prevent="selectCategory(categories[activeCategory].name, sub)"
              >
                {{ sub }}
              </a>
            </li>
          </ul>
        </div>


        <div class="drawer-mobile-auth">
          <div v-if="currentUser" class="mobile-user-card">
            <div class="mobile-user-info" @click="closeCatalog(); emit('open-account')">
              <span class="mobile-user-name">{{ currentUser.name }}</span>
              <span v-if="currentUser.role === 'wholesale'" class="user-badge wholesale">
                Опт • УНП {{ currentUser.unp }}
              </span>
              <span v-else class="user-badge">Розничный покупатель</span>
            </div>
            <button 
              type="button" 
              class="btn-logout mobile-logout-btn" 
              @click="closeCatalog(); emit('logout')"
            >
              Выйти
            </button>
          </div>

          <button 
            v-else
            type="button" 
            class="btn-login full-btn" 
            @click="closeCatalog(); emit('open-auth', 'login')"
          >
            Войти или зарегистрироваться
          </button>
        </div>
      </div>
    </aside>
  </Transition>
</template>

<style scoped>
.header {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 100;
  background-color: #0f172a;
  color: #f8fafc;
  border-bottom: 1px solid rgba(163, 210, 249, 0.25);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.2);
}

.container {
  width: 100%;
  padding: 12px 24px;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.logo-slot {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
color: inherit;
flex-shrink: 0;
}
.logo-placeholder {
width: 42px;
height: 42px;
border: 2px dashed #A3D2F9;
border-radius: 10px;
display: flex;
align-items: center;
justify-content: center;
font-size: 11px;
font-weight: 700;
color: #A3D2F9;
}
.brand-name {
font-size: 20px;
font-weight: 800;
letter-spacing: 0.5px;
}
.brand-accent {
color: #f59e0b;
}
.search-group {
flex: 1;
max-width: 780px;
display: flex;
align-items: center;
gap: 10px;
min-width: 0;
}


.wb-catalog-btn {
width: 46px;
height: 46px;
border-radius: 12px;
border: 1.5px solid rgba(163, 210, 249, 0.55);
background-color: rgba(163, 210, 249, 0.08);
color: #ffffff;
display: inline-flex;
align-items: center;
justify-content: center;
cursor: pointer;
transition: all 0.2s ease;
flex-shrink: 0;
}
.wb-catalog-btn:hover,
.wb-catalog-btn.is-active {
background-color: #A3D2F9;
border-color: #A3D2F9;
color: #0f172a;
}
.search-bar {
flex: 1;
height: 46px;
background-color: #ffffff;
border-radius: 14px;
display: flex;
align-items: center;
padding: 0 6px 0 16px;
border: 2px solid transparent;
transition: border-color 0.2s ease, box-shadow 0.2s ease;
min-width: 0;
}
.search-bar:focus-within {
border-color: #A3D2F9;
box-shadow: 0 0 0 3px rgba(163, 210, 249, 0.35);
}
.search-input {
flex: 1;
width: 100%;
min-width: 0;
border: none;
outline: none;
background: transparent;
font-size: 15px;
color: #0f172a;
}
.search-input::placeholder {
color: #94a3b8;
}
.search-clear {
background: transparent;
border: none;
color: #94a3b8;
font-size: 14px;
padding: 4px 8px;
cursor: pointer;
}
.search-clear:hover {
color: #0f172a;
}
.search-submit {
width: 36px;
height: 36px;
border-radius: 10px;
border: none;
background-color: #A3D2F9;
color: #0f172a;
display: inline-flex;
align-items: center;
justify-content: center;
cursor: pointer;
transition: background-color 0.2s ease;
flex-shrink: 0;
}
.search-submit:hover {
background-color: #7cc0f8;
}
.header-actions {
display: flex;
align-items: center;
gap: 12px;
flex-shrink: 0;
}
.auth-buttons {
display: flex;
align-items: center;
gap: 10px;
}
.btn-login {
height: 44px;
display: inline-flex;
align-items: center;
justify-content: center;
gap: 8px;
padding: 0 18px;
border-radius: 12px;
font-size: 14px;
font-weight: 700;
cursor: pointer;
background-color: #A3D2F9;
color: #0f172a;
border: 1px solid #A3D2F9;
transition: background-color 0.2s ease, transform 0.1s ease;
white-space: nowrap;
}
.btn-login:hover {
background-color: #82c2f7;
}
.btn-login:active {
transform: scale(0.98);
}
/* Плашка профиля вошедшего пользователя */
.user-profile-pill {
height: 44px;
display: inline-flex;
align-items: center;
gap: 10px;
padding: 0 8px 0 10px;
border-radius: 12px;
background-color: #1e293b;
border: 1px solid rgba(163, 210, 249, 0.35);
}
.user-avatar {
width: 28px;
height: 28px;
border-radius: 8px;
background-color: rgba(163, 210, 249, 0.15);
display: flex;
align-items: center;
justify-content: center;
font-size: 14px;
flex-shrink: 0;
}
.user-avatar.wholesale {
background-color: rgba(245, 158, 11, 0.2);
}
.user-meta {
display: flex;
flex-direction: column;
justify-content: center;
max-width: 150px;
line-height: 1.15;
}
.user-name {
font-size: 13px;
font-weight: 700;
color: #f8fafc;
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
}
.user-badge {
font-size: 10px;
font-weight: 600;
color: #94a3b8;
}
.user-badge.wholesale {
color: #A3D2F9;
}
.btn-logout {
height: 30px;
padding: 0 10px;
border-radius: 8px;
border: 1px solid #475569;
background-color: transparent;
color: #cbd5e1;
font-size: 12px;
font-weight: 600;
cursor: pointer;
transition: all 0.2s ease;
white-space: nowrap;
}
.btn-logout:hover {
background-color: #ef4444;
border-color: #ef4444;
color: #ffffff;
}
.btn-cart {
height: 44px;
display: inline-flex;
align-items: center;
gap: 8px;
padding: 0 14px;
background-color: #1e293b;
color: #f8fafc;
border: none;
border-radius: 12px;
cursor: pointer;
font-size: 14px;
font-weight: 600;
transition: background-color 0.2s ease;
}
.btn-cart:hover {
background-color: #334155;
}
.cart-badge {
background-color: #f59e0b;
color: #0f172a;
font-size: 12px;
font-weight: 800;
min-width: 20px;
height: 20px;
padding: 0 6px;
border-radius: 999px;
display: inline-flex;
align-items: center;
justify-content: center;
}
.drawer-backdrop {
position: fixed;
inset: 0;
background-color: rgba(15, 23, 42, 0.55);
backdrop-filter: blur(2px);
z-index: 150;
}
.catalog-drawer {
position: fixed;
top: 0;
left: 0;
bottom: 0;
width: 640px;
max-width: 92vw;
background-color: #ffffff;
color: #0f172a;
z-index: 200;
box-shadow: 8px 0 30px rgba(15, 23, 42, 0.25);
display: flex;
flex-direction: column;
}
.drawer-header {
display: flex;
align-items: center;
justify-content: space-between;
padding: 18px 24px;
background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
color: #ffffff;
}
.drawer-title {
font-size: 18px;
font-weight: 700;
}
.drawer-close {
width: 36px;
height: 36px;
border-radius: 10px;
border: 1px solid rgba(255, 255, 255, 0.2);
background: transparent;
color: #ffffff;
font-size: 16px;
cursor: pointer;
}
.drawer-close:hover {
background-color: rgba(255, 255, 255, 0.1);
}
.drawer-body {
display: flex;
flex: 1;
overflow-y: auto;
}
.category-list {
width: 280px;
list-style: none;
background-color: #f1f5f9;
border-right: 1px solid #e2e8f0;
padding: 12px 0;
flex-shrink: 0;
}
.category-item {
display: flex;
align-items: center;
gap: 12px;
padding: 14px 20px;
cursor: pointer;
font-size: 15px;
font-weight: 500;
transition: all 0.15s ease;
}
.category-item:hover,
.category-item.active {
background-color: #A3D2F9;
color: #0f172a;
font-weight: 700;
}
.cat-icon {
font-size: 18px;
}
.cat-name {
flex: 1;
}
.cat-arrow {
font-size: 18px;
opacity: 0.6;
}
.subcategory-panel {
flex: 1;
padding: 24px;
}
.subcat-title {
font-size: 18px;
font-weight: 700;
margin-bottom: 16px;
color: #0f172a;
padding-bottom: 10px;
border-bottom: 2px solid #A3D2F9;
}
.subcat-list {
list-style: none;
display: flex;
flex-direction: column;
gap: 12px;
}
.subcat-link {
text-decoration: none;
color: #334155;
font-size: 15px;
transition: color 0.15s ease;
}
.subcat-link:hover {
color: #0284c7;
font-weight: 600;
}
.all-cat-link {
font-weight: 700;
color: #0284c7;
}
.drawer-mobile-auth {
display: none;
}
.fade-enter-active,
.fade-leave-active {
transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
opacity: 0;
}
.slide-left-enter-active,
.slide-left-leave-active {
transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-left-enter-from,
.slide-left-leave-to {
transform: translateX(-100%);
}
@media (max-width: 960px) {
.auth-buttons {
display: none;
}
.drawer-body {
flex-direction: column;
}
.category-list {
width: 100%;
border-right: none;
border-bottom: 1px solid #e2e8f0;
}
.drawer-mobile-auth {
display: grid;
grid-template-columns: 1fr;
padding: 16px 20px;
margin-top: auto;
background-color: #0f172a;
}
.full-btn {
width: 100%;
}
.mobile-user-card {
display: flex;
align-items: center;
justify-content: space-between;
gap: 12px;
padding: 10px 12px;
border-radius: 12px;
background-color: #1e293b;
border: 1px solid rgba(163, 210, 249, 0.3);
}
.mobile-user-info {
display: flex;
flex-direction: column;
gap: 3px;
min-width: 0;
}
.mobile-user-name {
font-size: 14px;
font-weight: 700;
color: #ffffff;
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
}
.mobile-logout-btn {
height: 34px;
padding: 0 14px;
}
}

.user-clickable-area { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; }

@media (max-width: 680px) {
.container {
padding: 10px 14px;
}
.header-inner {
flex-wrap: wrap;
row-gap: 10px;
column-gap: 10px;
}
.logo-slot {
order: 1;
}
.header-actions {
order: 2;
margin-left: auto;
}
.search-group {
order: 3;
flex: 0 0 100%;
width: 100%;
max-width: 100%;
gap: 8px;
}
.wb-catalog-btn {
width: 42px;
height: 42px;
}
.search-bar {
height: 42px;
padding-left: 12px;
}
.brand-name {
font-size: 17px;
}
.cart-text {
display: none;
}
}

@media (min-width: 961px) {
  .wb-catalog-btn {
    display: none !important;
  }
}

/* На ПК меню и поиск находятся в каталоге, а на мобильных остаются в шапке */
@media (min-width: 961px) {
  .search-group {
    display: none !important;
  }
}

.desktop-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: rgba(30, 41, 59, 0.75);
  padding: 5px;
  border-radius: 14px;
  border: 1px solid rgba(163, 210, 249, 0.2);
}

.nav-pill {
  height: 36px;
  padding: 0 16px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: all 0.18s ease;
}

.nav-pill:hover {
  color: #ffffff;
  background-color: rgba(163, 210, 249, 0.14);
}

.nav-pill.active {
  background-color: #A3D2F9;
  color: #0f172a;
  box-shadow: 0 2px 8px rgba(163, 210, 249, 0.35);
}

@media (max-width: 960px) {
  .desktop-nav {
    display: none;
  }
}


</style>