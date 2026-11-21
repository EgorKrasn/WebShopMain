<script setup>
import { ref } from 'vue'

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  },
  selectedCategory: {
    type: String,
    default: ''
  },
  selectedSubcategory: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select-category'])

const hoveredCategoryId = ref(null)

const handleSelect = (categoryName, subcategoryName = '') => {
  emit('select-category', {
    category: categoryName,
    subcategory: subcategoryName
  })
  hoveredCategoryId.value = null
}
</script>

<template>
  <aside class="desktop-sidebar" aria-label="Категории товаров">
    <div class="sidebar-card">
      <div class="sidebar-header">
        <span class="sidebar-header-icon">☰</span>
        <span class="sidebar-header-title">Каталог товаров</span>
      </div>

      <ul class="sidebar-list">
        <!-- Пункт: Все товары -->
        <li>
          <button
            type="button"
            class="sidebar-item"
            :class="{ active: !selectedCategory }"
            @click="handleSelect('', '')"
          >
            <span class="item-icon">📋</span>
            <span class="item-name">Все товары каталога</span>
          </button>
        </li>

        <li class="sidebar-divider"></li>


        <!-- Динамические категории из БД -->
        <li
          v-for="cat in categories"
          :key="cat.id"
          class="sidebar-cat-wrapper"
          @mouseenter="hoveredCategoryId = cat.id"
          @mouseleave="hoveredCategoryId = null"
        >
          <button
            type="button"
            class="sidebar-item"
            :class="{ active: selectedCategory === cat.name }"
            @click="handleSelect(cat.name, '')"
          >
            <span class="item-icon">{{ cat.icon || '⌚' }}</span>
            <span class="item-name">{{ cat.name }}</span>
            <span
              v-if="cat.subcategories && cat.subcategories.length > 0"
              class="item-arrow"
            >
              ›
            </span>
          </button>

          <!-- Всплывающая панель подкатегорий справа при наведении -->
          <div
            v-if="hoveredCategoryId === cat.id && cat.subcategories && cat.subcategories.length > 0"
            class="flyout-panel"
          >
            <div class="flyout-title">{{ cat.name }}</div>
            <ul class="flyout-list">
              <li>
                <button
                  type="button"
                  class="flyout-link all-link"
                  @click="handleSelect(cat.name, '')"
                >
                  Все модели раздела →
                </button>
              </li>
              <li v-for="sub in cat.subcategories" :key="sub">
                <button
                  type="button"
                  class="flyout-link"
                  :class="{ 'sub-active': selectedCategory === cat.name && selectedSubcategory === sub }"
                  @click="handleSelect(cat.name, sub)"
                >
                  {{ sub }}
                </button>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.desktop-sidebar {
  width: 270px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
  align-self: flex-start;
  z-index: 40;
}

.sidebar-card {
  background-color: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
  overflow: visible;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 18px;
  background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
  color: #ffffff;
  border-radius: 18px 18px 0 0;
  font-size: 15px;
  font-weight: 800;
}

.sidebar-header-icon {
  color: #A3D2F9;
  font-size: 16px;
}

.sidebar-list {
  list-style: none;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sidebar-divider {
  height: 1px;
  background-color: #e2e8f0;
  margin: 6px 8px;
}

.sidebar-cat-wrapper {
  position: relative;
}

.sidebar-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 12px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #0f172a;
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: all 0.16s ease;
}

.sidebar-item:hover {
  background-color: #e0f2fe;
  color: #0f172a;
}

.sidebar-item.active {
  background-color: #0f172a;
  color: #A3D2F9;
  font-weight: 700;
}

.item-icon {
  font-size: 17px;
  width: 22px;
  text-align: center;
  flex-shrink: 0;
}

.item-name {
  flex: 1;
  line-height: 1.3;
}

.item-arrow {
  font-size: 18px;
  opacity: 0.55;
  font-weight: 700;
}

.sidebar-item:hover .item-arrow {
  opacity: 1;
  transform: translateX(2px);
}

/* Всплывающее меню подкатегорий справа */
.flyout-panel {
  position: absolute;
  top: -4px;
  left: calc(100% + 8px);
  width: 260px;
  background-color: #ffffff;
  border-radius: 16px;
  padding: 16px;
  border: 1px solid #cbd5e1;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.18);
  z-index: 60;
}

/* Невидимый мостик, чтобы курсор не терял фокус при переходе в панель */
.flyout-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: -12px;
  width: 12px;
  height: 100%;
}

.flyout-title {
  font-size: 15px;
  font-weight: 800;
  color: #0f172a;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 2px solid #A3D2F9;
}

.flyout-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.flyout-link {
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: #334155;
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.flyout-link:hover {
  background-color: #f1f5f9;
  color: #0284c7;
  font-weight: 700;
}

.flyout-link.all-link {
  color: #0284c7;
  font-weight: 700;
}

.flyout-link.sub-active {
  background-color: #e0f2fe;
  color: #0f172a;
  font-weight: 700;
}

/* Скрываем на планшетах и телефонах (там работает мобильный drawer в Navbar) */
@media (max-width: 960px) {
  .desktop-sidebar {
    display: none;
  }
}
</style>
