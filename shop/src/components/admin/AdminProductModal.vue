<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Copy, ClipboardPaste, Upload, Layers, EyeOff } from 'lucide-vue-next'

import { api, resolveImageUrl } from '../../services/api.js'
import { useBackdropClose } from '../../composables/useBackdropClose.js'
import './admin.css'


const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'create' // 'create' | 'edit' | 'duplicate'
  },
  product: {
    type: Object,
    default: null
  },
  categories: {
    type: Array,
    default: () => []
  },
  allProducts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'saved', 'toast', 'error'])

const backdrop = useBackdropClose(() => emit('close'))

const isUploadingImage = ref(false)
const isSaving = ref(false)

const applyToGroup = ref(false)
const groupSyncOptions = reactive({
  category: true,
  specsAndAttrs: true,
  pricesAndPromo: true
})

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
  minWholesaleQty: 5,
  stock: 10,
  isHidden: false,
  retailPrice: 0,
  wholesalePrice: 0,
  oldRetailPrice: null,
  oldWholesalePrice: null,
  promoLabel: '',
  discountPercent: 0,
  attributes: [
    { label: 'Механизм', value: 'Кварцевый' },
    { label: 'Материал', value: 'Пластик / Стекло' },
    { label: 'Гарантия', value: '12 месяцев' }
  ]
})

const generateUniqueCopySku = (baseSku) => {
  const cleanBase = String(baseSku || 'ST-NEW').trim()
  const existingSkus = new Set(props.allProducts.map((p) => p.sku.toLowerCase()))

  let candidate = `${cleanBase}-COPY`
  let counter = 2
  while (existingSkus.has(candidate.toLowerCase())) {
    candidate = `${cleanBase}-COPY-${counter}`
    counter++
  }
  return candidate
}

const initForm = () => {
  applyToGroup.value = false
  groupSyncOptions.category = true
  groupSyncOptions.specsAndAttrs = true
  groupSyncOptions.pricesAndPromo = true

  const defaultCategory = props.categories[0]?.name || 'Наручные часы'

  if (!props.product || props.mode === 'create') {
    Object.assign(productForm, {
      sku: '',
      groupId: '',
      colorName: '',
      category: defaultCategory,
      subcategory: '',
      name: '',
      specs: '',
      description: '',
      image: '',
      icon: '⌚',
      retailPrice: 25,
      wholesalePrice: 16,
      minWholesaleQty: 10,
      stock: 20,
      isHidden: false,
      oldRetailPrice: null,
      oldWholesalePrice: null,
      promoLabel: '',
      discountPercent: 0,
      attributes: [
        { label: 'Механизм', value: 'Кварцевый' },
        { label: 'Материал', value: 'Пластик' },
        { label: 'Гарантия', value: '12 месяцев' }
      ]
    })
    return
  }

  const p = props.product
  const isDuplicate = props.mode === 'duplicate'
  const existingAttrs =
    Array.isArray(p.attributes) && p.attributes.length > 0
      ? p.attributes.map((a) => ({ label: a.label, value: a.value }))
      : [
          { label: 'Механизм', value: p.mechanism || '' },
          { label: 'Материал', value: p.caseMaterial || '' },
          { label: 'Гарантия', value: p.warranty || '12 месяцев' }
        ]

  Object.assign(productForm, {
    sku: isDuplicate ? generateUniqueCopySku(p.sku) : p.sku || '',
    groupId: p.groupId || '',
    colorName: p.colorName || '',
    category: p.category || defaultCategory,
    subcategory: p.subcategory || '',
    name: isDuplicate && p.name ? `${p.name} (копия)` : p.name || '',
    specs: p.specs || '',
    description: p.description || '',
    image: p.image || '',
    icon: p.icon || '⌚',
    retailPrice: p.retailPrice || 0,
    wholesalePrice: p.wholesalePrice || 0,
    minWholesaleQty: p.minWholesaleQty || 5,
    stock: p.stock ?? 0,
    isHidden: Boolean(p.isHidden),
    oldRetailPrice: p.oldRetailPrice || null,
    oldWholesalePrice: p.oldWholesalePrice || null,
    promoLabel: p.promoLabel || '',
    discountPercent: p.discountPercent || 0,
    attributes: existingAttrs
  })
}
watch(
  () => [props.isOpen, props.mode, props.product],
  ([opened]) => {
    if (opened) {
      initForm()
    }
  },
  { immediate: true }
)

const availableSubcategories = computed(() => {
  const found = props.categories.find((c) => c.name === productForm.category)
  return found?.subcategories || []
})

const siblingGroupProducts = computed(() => {
  const gid = String(productForm.groupId || '').trim().toLowerCase()
  if (!gid) return []
  const currentId = props.mode === 'edit' ? props.product?.id : null
  return props.allProducts.filter(
    (item) => item.id !== currentId && String(item.groupId || '').trim().toLowerCase() === gid
  )
})

const addAttributeRow = () => {
  productForm.attributes.push({ label: '', value: '' })
}

const removeAttributeRow = (index) => {
  productForm.attributes.splice(index, 1)
}

const ATTR_CLIPBOARD_KEY = 'sandrintime_copied_attributes'
const copiedAttributes = ref([])

try {
  const savedAttrs = localStorage.getItem(ATTR_CLIPBOARD_KEY)
  if (savedAttrs) {
    const parsed = JSON.parse(savedAttrs)
    if (Array.isArray(parsed)) {
      copiedAttributes.value = parsed
    }
  }
} catch {
  // игнорируем повреждённый JSON
}

const copyProductAttributes = () => {
  const validAttrs = productForm.attributes
    .map((a) => ({
      label: String(a.label || '').trim(),
      value: String(a.value || '').trim()
    }))
    .filter((a) => a.label || a.value)

  if (validAttrs.length === 0) {
    emit('error', 'Нет заполненных характеристик для копирования')
    return
  }

  copiedAttributes.value = validAttrs
  try {
    localStorage.setItem(ATTR_CLIPBOARD_KEY, JSON.stringify(validAttrs))
  } catch {
    // игнорируем ошибки квоты storage
  }
  emit('toast', `Скопировано характеристик: ${validAttrs.length} шт.`)
}

const pasteProductAttributes = () => {
  if (!Array.isArray(copiedAttributes.value) || copiedAttributes.value.length === 0) {
    emit('error', 'Буфер характеристик пуст — сначала нажмите «Копировать»')
    return
  }

  productForm.attributes = copiedAttributes.value.map((a) => ({
    label: a.label,
    value: a.value
  }))
  emit('toast', `Вставлено характеристик: ${productForm.attributes.length} шт.`)
}

const handleImageFileUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  isUploadingImage.value = true
  emit('error', '')
  try {
    const res = await api.adminUploadImage(file)
    if (res?.url) {
      productForm.image = res.url
      emit('toast', 'Фото загружено')
    }
  } catch (err) {
    emit('error', err.message || 'Не удалось загрузить фото')
  } finally {
    isUploadingImage.value = false
    event.target.value = ''
  }
}

const onDiscountPercentInput = () => {
  const pct = Number(productForm.discountPercent)

  if (!pct || pct <= 0) {
    if (productForm.oldRetailPrice && productForm.oldRetailPrice > productForm.retailPrice) {
      productForm.retailPrice = Number(productForm.oldRetailPrice)
    }
    productForm.oldRetailPrice = null

    if (productForm.oldWholesalePrice && productForm.oldWholesalePrice > productForm.wholesalePrice) {
      productForm.wholesalePrice = Number(productForm.oldWholesalePrice)
    }
    productForm.oldWholesalePrice = null
    return
  }

  const clampedPct = Math.min(pct, 99)
  productForm.discountPercent = clampedPct
  const multiplier = 1 - clampedPct / 100

  const baseRetail =
    productForm.oldRetailPrice && productForm.oldRetailPrice > 0
      ? Number(productForm.oldRetailPrice)
      : Number(productForm.retailPrice || 0)

  if (baseRetail > 0) {
    productForm.oldRetailPrice = baseRetail
    productForm.retailPrice = Number((baseRetail * multiplier).toFixed(2))
  }

  if (productForm.oldWholesalePrice && productForm.oldWholesalePrice > 0) {
    productForm.wholesalePrice = Number((Number(productForm.oldWholesalePrice) * multiplier).toFixed(2))
  }
}

const submitProductForm = async () => {
  emit('error', '')
  isSaving.value = true

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
    isHidden: Boolean(productForm.isHidden),
    attributes: cleanAttributes,
    oldRetailPrice: productForm.oldRetailPrice ? Number(productForm.oldRetailPrice) : null,
    oldWholesalePrice: productForm.oldWholesalePrice ? Number(productForm.oldWholesalePrice) : null,
    promoLabel: productForm.promoLabel || ''
  }

  try {
    if (props.mode === 'edit' && props.product?.id) {
      await api.adminUpdateProduct(props.product.id, payload)
    } else {
      await api.adminCreateProduct(payload)
    }

    let syncedCount = 0
    if (applyToGroup.value && siblingGroupProducts.value.length > 0) {
      const sharedPatch = {}

      if (groupSyncOptions.category) {
        sharedPatch.category = payload.category
        sharedPatch.subcategory = payload.subcategory
      }
      if (groupSyncOptions.specsAndAttrs) {
        sharedPatch.specs = payload.specs
        sharedPatch.description = payload.description
        sharedPatch.attributes = cleanAttributes
      }
      if (groupSyncOptions.pricesAndPromo) {
        sharedPatch.retailPrice = payload.retailPrice
        sharedPatch.wholesalePrice = payload.wholesalePrice
        sharedPatch.minWholesaleQty = payload.minWholesaleQty
        sharedPatch.oldRetailPrice = payload.oldRetailPrice
        sharedPatch.oldWholesalePrice = payload.oldWholesalePrice
        sharedPatch.promoLabel = payload.promoLabel
      }

      if (Object.keys(sharedPatch).length > 0) {
        await Promise.all(
          siblingGroupProducts.value.map((sibling) =>
            api.adminUpdateProduct(sibling.id, sharedPatch)
          )
        )
        syncedCount = siblingGroupProducts.value.length
      }
    }

    if (syncedCount > 0) {
      emit('toast', `Товар сохранён и синхронизирован с ${syncedCount} расцветками группы`)
    } else {
      emit('toast', props.mode === 'edit' ? 'Товар успешно обновлён' : 'Новый товар добавлен в каталог')
    }

    emit('saved')
    emit('close')
  } catch (err) {
    emit('error', err.message || 'Ошибка сохранения товара')
  } finally {
    isSaving.value = false
  }
}
</script>


<template>
  <div
    v-if="isOpen"
    class="modal-overlay"
    @mousedown.self="backdrop.onBackdropMouseDown"
    @mouseup.self="backdrop.onBackdropMouseUp"
  >
    <form class="product-editor-modal" @submit.prevent="submitProductForm">
      <div class="editor-head">
        <h3>
          {{
            mode === 'edit'
              ? 'Редактирование товара'
              : mode === 'duplicate'
                ? 'Создание копии товара'
                : 'Новый товар в каталог'
          }}
        </h3>
        <button type="button" class="close-editor" @click="emit('close')">✕</button>
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
              <option v-for="c in categories" :key="c.id" :value="c.name">
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

        <div v-if="siblingGroupProducts.length > 0" class="group-sync-box">
          <label class="group-sync-main-check">
            <input v-model="applyToGroup" type="checkbox" />
            <Layers :size="16" color="#0284c7" />
            <span>
              Применить общие параметры ко всем цветам группы
              <strong>(ещё {{ siblingGroupProducts.length }} шт.)</strong>
            </span>
          </label>

          <div v-if="applyToGroup" class="group-sync-options">
            <label class="sync-sub-check">
              <input v-model="groupSyncOptions.category" type="checkbox" />
              <span>Категория и подкатегория</span>
            </label>
            <label class="sync-sub-check">
              <input v-model="groupSyncOptions.specsAndAttrs" type="checkbox" />
              <span>Характеристики и описание</span>
            </label>
            <label class="sync-sub-check">
              <input v-model="groupSyncOptions.pricesAndPromo" type="checkbox" />
              <span>Цены, скидка и мин. опт</span>
            </label>
            <p class="group-sync-note">
              Артикул (SKU), название, цвет, фото и остаток у других расцветок останутся без изменений.
            </p>
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

        <div class="visibility-editor-box" :class="{ active: productForm.isHidden }">
          <label class="visibility-check-label">
            <input v-model="productForm.isHidden" type="checkbox" />
            <EyeOff :size="16" />
            <div>
              <strong>Скрыть товар из каталога (витрины)</strong>
              <span>
                Карточка останется в базе данных и админке, но покупатели не увидят её на сайте и не смогут оформить заказ.
              </span>
            </div>
          </label>
        </div>

        <div class="promo-editor-box">

          <div class="promo-editor-title">Скидка и акция (необязательно)</div>
          <div class="form-grid-4">
            <div class="f-group">
              <label>Скидка (%)</label>
              <input
                v-model.number="productForm.discountPercent"
                type="number"
                min="0"
                max="99"
                step="1"
                placeholder="Напр. 20"
                @input="onDiscountPercentInput"
              />
            </div>
            <div class="f-group">
              <label>Старая розн. цена (BYN)</label>
              <input
                v-model.number="productForm.oldRetailPrice"
                type="number"
                step="0.01"
                min="0"
                placeholder="Авто"
              />
            </div>
            <div class="f-group">
              <label>Старая опт. цена (BYN)</label>
              <input
                v-model.number="productForm.oldWholesalePrice"
                type="number"
                step="0.01"
                min="0"
                placeholder="Необяз."
              />
            </div>
            <div class="f-group">
              <label>Бейдж акции (текст)</label>
              <input
                v-model="productForm.promoLabel"
                type="text"
                maxlength="24"
                placeholder="Авто (-20%)"
              />
            </div>
          </div>
        </div>

        <div class="attrs-editor">
          <div class="attrs-head">
            <label>Характеристики в карточке (названия полей можно менять):</label>
            <div class="attrs-head-actions">
              <button
                type="button"
                class="btn-attr-tool copy"
                title="Скопировать все характеристики этого товара"
                @click="copyProductAttributes"
              >
                <Copy :size="13" />
                <span>Копировать</span>
              </button>
              <button
                type="button"
                class="btn-attr-tool paste"
                :disabled="copiedAttributes.length === 0"
                :title="
                  copiedAttributes.length > 0
                    ? `Вставить скопированные характеристики (${copiedAttributes.length} шт.)`
                    : 'Сначала скопируйте характеристики из другого товара'
                "
                @click="pasteProductAttributes"
              >
                <ClipboardPaste :size="13" />
                <span>Вставить{{ copiedAttributes.length > 0 ? ` (${copiedAttributes.length})` : '' }}</span>
              </button>
              <button type="button" class="btn-add-attr" @click="addAttributeRow">
                + Добавить поле
              </button>
            </div>
          </div>
          <div v-for="(attr, idx) in productForm.attributes" :key="idx" class="attr-row">
            <input v-model="attr.label" type="text" placeholder="Название поля (напр. Водозащита)" />
            <input v-model="attr.value" type="text" placeholder="Значение (напр. 5 ATM)" />
            <button type="button" class="btn-del-attr" @click="removeAttributeRow(idx)">✕</button>
          </div>
        </div>
      </div>

      <div class="editor-foot">
        <button type="button" class="btn-cancel" @click="emit('close')">Отмена</button>
        <button type="submit" class="btn-submit-prod" :disabled="isSaving">
          {{ isSaving ? 'Сохранение...' : 'Сохранить товар' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.group-sync-box {
  background-color: #f0f9ff;
  border: 1.5px solid #bae6fd;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-sync-main-check {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #0f172a;
  cursor: pointer;
}

.group-sync-main-check input[type="checkbox"],
.sync-sub-check input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #0284c7;
  cursor: pointer;
}

.group-sync-options {
  padding-left: 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sync-sub-check {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}

.group-sync-note {
  font-size: 11.5px;
  color: #64748b;
  margin-top: 2px;
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

.promo-editor-box {
  background-color: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.promo-editor-title {
  font-size: 12px;
  font-weight: 800;
  color: #92400e;
}

.attrs-head-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.btn-attr-tool {
  height: 26px;
  padding: 0 9px;
  border-radius: 7px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}

.btn-attr-tool.copy {
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #334155;
}

.btn-attr-tool.copy:hover {
  border-color: #0f172a;
  background-color: #f1f5f9;
  color: #0f172a;
}

.btn-attr-tool.paste {
  border: 1px solid #c4b5fd;
  background-color: #f5f3ff;
  color: #6d28d9;
}

.btn-attr-tool.paste:hover:not(:disabled) {
  background-color: #7c3aed;
  border-color: #7c3aed;
  color: #ffffff;
}

.btn-attr-tool:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.visibility-editor-box {
  background-color: #f8fafc;
  border: 1.5px solid #cbd5e1;
  border-radius: 12px;
  padding: 11px 14px;
  transition: all 0.15s ease;
}

.visibility-editor-box.active {
  background-color: #fef3c7;
  border-color: #f59e0b;
}

.visibility-check-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  color: #0f172a;
}

.visibility-check-label input[type="checkbox"] {
  width: 17px;
  height: 17px;
  margin-top: 2px;
  accent-color: #d97706;
  cursor: pointer;
  flex-shrink: 0;
}

.visibility-check-label strong {
  display: block;
  font-size: 13px;
}

.visibility-check-label span {
  display: block;
  font-size: 11.5px;
  color: #475569;
  margin-top: 2px;
  line-height: 1.4;
}

</style>
