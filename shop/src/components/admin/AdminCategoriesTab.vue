<script setup>
import { ref, reactive } from 'vue'
import { Pencil, Trash2 } from 'lucide-vue-next'
import CategoryIcon from '../CategoryIcon.vue'
import { api } from '../../services/api.js'
import { useBackdropClose } from '../../composables/useBackdropClose.js'
import './admin.css'

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['updated', 'toast', 'error'])

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

const isCategoryFormOpen = ref(false)
const editingCategoryId = ref(null)
const categoryForm = reactive({
  name: '',
  icon: 'watch',
  sortOrder: 0,
  subcategories: ['']
})

const categoryBackdrop = useBackdropClose(() => {
  isCategoryFormOpen.value = false
})

const openCreateCategoryModal = () => {
  editingCategoryId.value = null
  Object.assign(categoryForm, {
    name: '',
    icon: 'watch',
    sortOrder: props.categories.length + 1,
    subcategories: ['']
  })
  isCategoryFormOpen.value = true
}

const openEditCategoryModal = (cat) => {
  editingCategoryId.value = cat.id
  Object.assign(categoryForm, {
    name: cat.name,
    icon: cat.icon || 'watch',
    sortOrder: cat.sortOrder || 0,
    subcategories:
      Array.isArray(cat.subcategories) && cat.subcategories.length > 0
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
  emit('error', '')
  const payload = {
    name: categoryForm.name,
    icon: categoryForm.icon,
    sortOrder: Number(categoryForm.sortOrder),
    subcategories: categoryForm.subcategories.filter((s) => s.trim())
  }
  try {
    if (editingCategoryId.value) {
      await api.adminUpdateCategory(editingCategoryId.value, payload)
      emit('toast', 'Категория обновлена')
    } else {
      await api.adminCreateCategory(payload)
      emit('toast', 'Категория создана')
    }
    isCategoryFormOpen.value = false
    emit('updated')
  } catch (err) {
    emit('error', err.message || 'Ошибка сохранения категории')
  }
}

const deleteCategoryItem = async (cat) => {
  if (!confirm(`Удалить категорию «${cat.name}»?`)) return
  emit('error', '')
  try {
    await api.adminDeleteCategory(cat.id)
    emit('updated')
    emit('toast', 'Категория удалена')
  } catch (err) {
    emit('error', err.message || 'Ошибка удаления категории')
  }
}
</script>

<template>
  <div class="tab-content">
    <div class="products-toolbar">
      <div style="font-size: 14px; color: #334155; font-weight: 600;">
        Управление разделами бокового меню каталога
      </div>
      <button type="button" class="btn-add-product" @click="openCreateCategoryModal">
        + Добавить категорию
      </button>
    </div>

    <div class="cards-grid">
      <article v-for="cat in categories" :key="cat.id" class="admin-card">
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

    <!-- Модальное окно редактора категории -->
    <div
      v-if="isCategoryFormOpen"
      class="modal-overlay"
      @mousedown.self="categoryBackdrop.onBackdropMouseDown"
      @mouseup.self="categoryBackdrop.onBackdropMouseUp"
    >
      <form class="product-editor-modal" @submit.prevent="submitCategoryForm">
        <div class="editor-head">
          <h3>{{ editingCategoryId ? 'Редактирование категории' : 'Новая категория' }}</h3>
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
            <div
              v-for="(sub, idx) in categoryForm.subcategories"
              :key="idx"
              class="attr-row"
              style="grid-template-columns: 1fr 32px;"
            >
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
  </div>
</template>

<style scoped>
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
</style>
