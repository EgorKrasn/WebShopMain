<script setup>
import { ref, computed } from 'vue'
import XLSX from 'xlsx-js-style'

import {
  FileSpreadsheet,
  Upload,
  Download,
  RefreshCw,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  X
} from 'lucide-vue-next'
import { api } from '../../services/api.js'
import { saveWorkbookCrossPlatform } from '../../utils/excelExport.js'
import './admin.css'

const props = defineProps({
  products: {
    type: Array,
    default: () => []
  },
  categories: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['updated', 'toast', 'error'])

const mode = ref('update')

// ==========================================
// РЕЖИМ 1: ОБНОВЛЕНИЕ ЦЕН И ОСТАТКОВ
// ==========================================
const stockMode = ref('add')
const updateFileInput = ref(null)
const updateFileName = ref('')
const parsedUpdateRows = ref([])
const isApplyingUpdate = ref(false)
const isReplaceConfirmOpen = ref(false)

const productsBySku = computed(() => {
  const map = new Map()
  for (const p of props.products) {
    if (p.sku) {
      map.set(String(p.sku).trim().toLowerCase(), p)
    }
  }
  return map
})

const parseOptionalNumber = (raw) => {
  if (raw === undefined || raw === null) return null
  const str = String(raw).trim().replace(',', '.')
  if (str === '') return null
  const num = Number(str)
  return Number.isFinite(num) ? num : null
}

const parseOptionalInt = (raw) => {
  if (raw === undefined || raw === null) return null
  const str = String(raw).trim().replace(',', '.')
  if (str === '') return null
  const num = Number(str)
  return Number.isFinite(num) ? Math.trunc(num) : null
}

const getStockStatusLabel = (stockQty) => {
  const qty = Number(stockQty ?? 0)
  if (qty <= 0) return 'Нет в наличии (0)'
  if (qty <= 3) return 'Мало (≤ 3 шт.)'
  return 'В наличии'
}

const downloadUpdateTemplate = async () => {
  const sourceList =
    props.products && props.products.length > 0
      ? props.products
      : [
          {
            sku: 'ST-1111',
            name: 'Пример товара',
            colorName: 'Чёрный',
            category: 'Наручные часы',
            retailPrice: 100,
            wholesalePrice: 70,
            stock: 10
          }
        ]

  const rows = sourceList.map((p, index) => ({
    '№': index + 1,
    'Артикул (SKU)*': p.sku || '',
    'Наименование (справочно)': p.name || '',
    'Цвет': p.colorName || '—',
    'Категория (справочно)': p.category || '',
    'Статус склада': getStockStatusLabel(p.stock),
    'Текущая розница (BYN)': Number(p.retailPrice || 0),
    'Новая розничная цена (BYN)': '',
    'Текущий опт (BYN)': Number(p.wholesalePrice || 0),
    'Новая оптовая цена (BYN)': '',
    'Текущий остаток (шт.)': Number(p.stock ?? 0),
    'Остаток (прибавить или заменить, шт.)': ''
  }))

  const ws = XLSX.utils.json_to_sheet(rows)
  const lastRow = rows.length + 1

  ws['!autofilter'] = { ref: `A1:L${lastRow}` }
  ws['!freeze'] = { xSplit: 0, ySplit: 1 }

  ws['!cols'] = [
    { wch: 6 },   // A: №
    { wch: 18 },  // B: Артикул
    { wch: 36 },  // C: Наименование
    { wch: 16 },  // D: Цвет
    { wch: 24 },  // E: Категория
    { wch: 19 },  // F: Статус склада
    { wch: 22 },  // G: Текущая розница
    { wch: 26 },  // H: Новая розничная цена
    { wch: 20 },  // I: Текущий опт
    { wch: 24 },  // J: Новая оптовая цена
    { wch: 22 },  // K: Текущий остаток
    { wch: 34 }   // L: Остаток (изменение)
  ]

  // Форматирование чисел: G, H, I, J — цены (0.00), K, L — остатки (0)
  for (let r = 2; r <= lastRow; r++) {
    for (const col of ['G', 'H', 'I', 'J']) {
      if (ws[`${col}${r}`]) ws[`${col}${r}`].z = '0.00'
    }
    for (const col of ['K', 'L']) {
      if (ws[`${col}${r}`]) ws[`${col}${r}`].z = '0'
    }
  }

  const borderThin = {
    top: { style: 'thin', color: { rgb: '94A3B8' } },
    bottom: { style: 'thin', color: { rgb: '94A3B8' } },
    left: { style: 'thin', color: { rgb: '94A3B8' } },
    right: { style: 'thin', color: { rgb: '94A3B8' } }
  }

  const headerBaseStyle = {
    font: { bold: true, color: { rgb: 'FFFFFF' }, sz: 11 },
    alignment: { vertical: 'center', horizontal: 'center', wrapText: true },
    border: {
      top: { style: 'medium', color: { rgb: '0F172A' } },
      bottom: { style: 'medium', color: { rgb: '0F172A' } },
      left: { style: 'thin', color: { rgb: '475569' } },
      right: { style: 'thin', color: { rgb: '475569' } }
    }
  }

  const colsLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
  const oldValueCols = new Set([6, 8, 10])  // G, I, K — прежние значения
  const newValueCols = new Set([7, 9, 11])  // H, J, L — новые значения (зона ввода)

  ws['!rows'] = [{ hpt: 30 }, ...rows.map(() => ({ hpt: 21 }))]

  // Шапка (строка 1): колонки ввода H, J, L выделены тёмно-зелёным, остальные — тёмно-синим
  colsLetters.forEach((col, idx) => {
    const ref = `${col}1`
    if (!ws[ref]) return
    ws[ref].s = {
      ...headerBaseStyle,
      alignment: {
        vertical: 'center',
        horizontal: idx >= 1 && idx <= 4 ? 'left' : 'center',
        wrapText: true
      },
      fill: { fgColor: { rgb: newValueCols.has(idx) ? '14532D' : '0F172A' } }
    }
  })

  // Строки данных
  for (let r = 2; r <= lastRow; r++) {
    const isEven = r % 2 === 0
    const rowData = rows[r - 2]

    colsLetters.forEach((col, idx) => {
      const ref = `${col}${r}`
      if (!ws[ref]) ws[ref] = { t: 's', v: '' }

      let bgRgb = isEven ? 'E0F2FE' : 'FFFFFF'
      let fontStyle = { color: { rgb: '0F172A' }, sz: 10.5 }
      let horizontalAlign = 'left'

      if (idx === 0) {
        horizontalAlign = 'center'
      } else if (oldValueCols.has(idx)) {
        // Прежние значения: полужирные, по центру
        fontStyle = { color: { rgb: '0F172A' }, bold: true, sz: 10.5 }
        horizontalAlign = 'center'
      } else if (newValueCols.has(idx)) {
        // Новые значения: зелёная зона ввода, обычный шрифт, по центру
        bgRgb = isEven ? 'DCFCE7' : 'F0FDF4'
        fontStyle = { color: { rgb: '0F172A' }, bold: false, sz: 10.5 }
        horizontalAlign = 'center'
      } else if (idx === 5 && rowData) {
        // Статус склада
        horizontalAlign = 'center'
        const statusText = String(rowData['Статус склада'] || '')
        if (statusText.includes('Нет в наличии')) {
          bgRgb = 'FEE2E2'
          fontStyle = { color: { rgb: 'B91C1C' }, bold: true, sz: 10.5 }
        } else if (statusText.includes('Мало')) {
          bgRgb = 'FEF3C7'
          fontStyle = { color: { rgb: '92400E' }, bold: true, sz: 10.5 }
        } else {
          bgRgb = 'DCFCE7'
          fontStyle = { color: { rgb: '15803D' }, bold: true, sz: 10.5 }
        }
      }

      ws[ref].s = {
        fill: { fgColor: { rgb: bgRgb } },
        font: fontStyle,
        border: borderThin,
        alignment: {
          vertical: 'center',
          horizontal: horizontalAlign
        }
      }
    })
  }

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Цены и остатки')

  const today = new Date().toISOString().slice(0, 10)
  await saveWorkbookCrossPlatform(wb, `Template_Update_Prices_Stock_${today}.xlsx`)
}



const handleUpdateFileChange = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  emit('error', '')
  updateFileName.value = file.name
  parsedUpdateRows.value = []

  try {
    const buffer = await file.arrayBuffer()
    const wb = XLSX.read(buffer, { type: 'array' })
    const firstSheetName = wb.SheetNames[0]
    const ws = wb.Sheets[firstSheetName]
    const rawRows = XLSX.utils.sheet_to_json(ws, { defval: '' })

    const parsed = []
    for (const r of rawRows) {
      const sku = String(
        r['Артикул (SKU)*'] ?? r['Артикул'] ?? r['SKU'] ?? ''
      ).trim()
      if (!sku) continue

      const retailPrice = parseOptionalNumber(
        r['Новая розничная цена (BYN)'] ?? r['Новая розница']
      )
      const wholesalePrice = parseOptionalNumber(
        r['Новая оптовая цена (BYN)'] ?? r['Новый опт']
      )
      const stockValue = parseOptionalInt(
        r['Остаток (прибавить или заменить, шт.)'] ?? r['Остаток']
      )

      if (retailPrice === null && wholesalePrice === null && stockValue === null) {
        continue
      }

      const existing = productsBySku.value.get(sku.toLowerCase()) || null

      parsed.push({
        sku,
        found: Boolean(existing),
        name: existing ? existing.name : String(r['Наименование (справочно)'] || 'Артикул не найден в базе'),
        currentRetail: existing ? Number(existing.retailPrice || 0) : null,
        currentWholesale: existing ? Number(existing.wholesalePrice || 0) : null,
        currentStock: existing ? Number(existing.stock ?? 0) : null,
        retailPrice,
        wholesalePrice,
        stockValue
      })
    }

    if (parsed.length === 0) {
      emit('error', 'В загруженном файле не найдено ни одной заполненной строки с изменениями цен или остатков.')
      return
    }

    parsedUpdateRows.value = parsed
  } catch (err) {
    emit('error', 'Не удалось прочитать Excel-файл. Проверьте, что это корректный документ .xlsx')
  }
}

const validUpdateRows = computed(() => parsedUpdateRows.value.filter((r) => r.found))
const missingUpdateRows = computed(() => parsedUpdateRows.value.filter((r) => !r.found))
const stockAffectedCount = computed(
  () => validUpdateRows.value.filter((r) => r.stockValue !== null).length
)
const zeroStockReplaceCount = computed(
  () => validUpdateRows.value.filter((r) => r.stockValue === 0).length
)

const previewSearchQuery = ref('')

const filteredUpdatePreview = computed(() => {
  const q = previewSearchQuery.value.trim().toLowerCase()
  if (!q) return parsedUpdateRows.value
  return parsedUpdateRows.value.filter(
    (r) =>
      r.sku.toLowerCase().includes(q) ||
      r.name.toLowerCase().includes(q) ||
      (r.colorName && r.colorName.toLowerCase().includes(q))
  )
})


const calcPreviewStock = (row) => {
  if (!row.found || row.stockValue === null) return null
  if (stockMode.value === 'add') {
    return Math.max(0, (row.currentStock ?? 0) + row.stockValue)
  }
  return Math.max(0, row.stockValue)
}

const triggerApplyUpdate = () => {
  if (validUpdateRows.value.length === 0) return

  if (stockMode.value === 'replace' && stockAffectedCount.value > 0) {
    isReplaceConfirmOpen.value = true
    return
  }

  executeBulkUpdate()
}

const executeBulkUpdate = async () => {
  isReplaceConfirmOpen.value = false
  isApplyingUpdate.value = true
  emit('error', '')

  try {
    const payload = {
      stockMode: stockMode.value,
      items: validUpdateRows.value.map((r) => ({
        sku: r.sku,
        retailPrice: r.retailPrice,
        wholesalePrice: r.wholesalePrice,
        stockValue: r.stockValue
      }))
    }

    const res = await api.adminBulkUpdateProducts(payload)
    emit('updated')

    let msg = `Массовое обновление завершено: обновлено позиций — ${res.updatedCount}`
    if (res.notFoundSkus?.length) {
      msg += ` (не найдено SKU: ${res.notFoundSkus.length})`
    }
    emit('toast', msg)

    parsedUpdateRows.value = []
    updateFileName.value = ''
  } catch (err) {
    emit('error', err.message || 'Ошибка при массовом обновлении товаров')
  } finally {
    isApplyingUpdate.value = false
  }
}
// ==========================================
// РЕЖИМ 2: ДОБАВЛЕНИЕ НОВЫХ КАРТОЧЕК (БЕЗ ФОТО)
// ==========================================
const createFileInput = ref(null)
const createFileName = ref('')
const parsedCreateRows = ref([])
const isApplyingCreate = ref(false)
const createAsHidden = ref(true) // По умолчанию создаём скрытыми, пока не добавлены фото/цены

const categorySubcategoriesMap = computed(() => {
  const map = new Map()
  for (const c of props.categories || []) {
    const catName = String(c.name || '').trim()
    if (!catName) continue
    const subs = Array.isArray(c.subcategories)
      ? c.subcategories.map((s) => String(s).trim()).filter(Boolean)
      : []
    map.set(catName, new Set(subs))
  }
  return map
})


const validCategoryNames = computed(() => {
  return new Set((props.categories || []).map((c) => String(c.name).trim()))
})

const downloadCreateTemplate = async () => {
  const defaultCat = props.categories?.[0]?.name || 'Будильники'
  const defaultSub = props.categories?.[0]?.subcategories?.[0] || 'Стрелочные'

  // Обязательные колонки помечены звёздочкой (*)
  const sampleRows = [
    {
      'Артикул (SKU)*': 'ПРИМЕР-001',
      'Группа цвета (groupId)*': 'watch-classic',
      'Цвет*': 'Чёрный',
      'Категория*': defaultCat,
      'Подкатегория*': defaultSub,
      'Наименование*': 'Пример карточки (удалите или замените эту строку)',
      'Краткие характеристики': 'Кварцевый • Сталь • 5 ATM',
      'Описание': 'Подробное описание модели для карточки товара.',
      'Розничная цена (BYN)': 120.00,
      'Оптовая цена (BYN)': 85.00,
      'Мин. партия опт (шт.)': 5,
      'Начальный остаток (шт.)': 20,
      'Старая розница (BYN)': '',
      'Старый опт (BYN)': '',
      'Акционный бейдж': ''
    }
  ]

  const borderThin = {
    top: { style: 'thin', color: { rgb: '94A3B8' } },
    bottom: { style: 'thin', color: { rgb: '94A3B8' } },
    left: { style: 'thin', color: { rgb: '94A3B8' } },
    right: { style: 'thin', color: { rgb: '94A3B8' } }
  }

  const headerBorder = {
    top: { style: 'medium', color: { rgb: '0F172A' } },
    bottom: { style: 'medium', color: { rgb: '0F172A' } },
    left: { style: 'thin', color: { rgb: '475569' } },
    right: { style: 'thin', color: { rgb: '475569' } }
  }

  const wsProducts = XLSX.utils.json_to_sheet(sampleRows)
  const totalTemplateRows = 50
  wsProducts['!autofilter'] = { ref: `A1:O${totalTemplateRows}` }
  wsProducts['!freeze'] = { xSplit: 0, ySplit: 1 }
  wsProducts['!cols'] = [
    { wch: 19 }, // A: Артикул*
    { wch: 24 }, // B: Группа цвета*
    { wch: 16 }, // C: Цвет*
    { wch: 26 }, // D: Категория*
    { wch: 24 }, // E: Подкатегория*
    { wch: 38 }, // F: Наименование*
    { wch: 28 }, // G: Характеристики
    { wch: 34 }, // H: Описание
    { wch: 22 }, // I: Розница
    { wch: 20 }, // J: Опт
    { wch: 22 }, // K: Мин партия
    { wch: 22 }, // L: Начальный остаток
    { wch: 20 }, // M: Старая розница
    { wch: 18 }, // N: Старый опт
    { wch: 18 }  // O: Бейдж
  ]

  wsProducts['!rows'] = [
    { hpt: 30 },
    ...Array.from({ length: totalTemplateRows - 1 }, () => ({ hpt: 21 }))
  ]

  const prodCols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O']

  // Шапка: первые 6 обязательных колонок (A:F) — насыщенный сине-бордовый акцент, остальные — тёмно-синий
  prodCols.forEach((col, idx) => {
    const ref = `${col}1`
    if (!wsProducts[ref]) return
    const isRequiredCol = idx <= 5
    wsProducts[ref].s = {
      fill: { fgColor: { rgb: isRequiredCol ? '1E3A8A' : '0F172A' } },
      font: { bold: true, color: { rgb: isRequiredCol ? 'FDE047' : 'FFFFFF' }, sz: 11 },
      alignment: { vertical: 'center', horizontal: 'left', wrapText: true },
      border: headerBorder
    }
  })

  // Строка 2 (ПРИМЕР-001) — мягкая жёлтая подсветка образца
  prodCols.forEach((col) => {
    const ref = `${col}2`
    if (!wsProducts[ref]) wsProducts[ref] = { t: 's', v: '' }
    wsProducts[ref].s = {
      fill: { fgColor: { rgb: 'FEF9C3' } },
      font: { color: { rgb: '713F12' }, italic: true, sz: 10.5 },
      border: borderThin,
      alignment: { vertical: 'center', horizontal: 'left' }
    }
  })

  // Строки 3..50 — полосатая зебра с рамками (обязательные колонки A:F чуть теплее/заметнее)
  for (let r = 3; r <= totalTemplateRows; r++) {
    const isEven = r % 2 === 0
    prodCols.forEach((col, idx) => {
      const ref = `${col}${r}`
      if (!wsProducts[ref]) wsProducts[ref] = { t: 's', v: '' }
      const isRequiredCol = idx <= 5
      let bgRgb = isEven ? 'EFF6FF' : 'FFFFFF'
      if (isRequiredCol) {
        bgRgb = isEven ? 'DBEAFE' : 'F8FAFC'
      }
      wsProducts[ref].s = {
        fill: { fgColor: { rgb: bgRgb } },
        font: { color: { rgb: '0F172A' }, sz: 10.5 },
        border: borderThin,
        alignment: { vertical: 'center', horizontal: 'left' }
      }
    })
  }

  // Лист 2: Справочник категорий и подкатегорий
  const catReferenceRows = (props.categories || []).map((c, idx) => ({
    '№': idx + 1,
    'Допустимая категория (копируйте точное название)': c.name,
    'Допустимые подкатегории': Array.isArray(c.subcategories) ? c.subcategories.join(', ') : ''
  }))
  const finalCatRows =
    catReferenceRows.length > 0
      ? catReferenceRows
      : [{ '№': 1, 'Допустимая категория (копируйте точное название)': 'Будильники', 'Допустимые подкатегории': 'Стрелочные' }]

  const lastCatRow = finalCatRows.length + 1
  const wsCats = XLSX.utils.json_to_sheet(finalCatRows)
  wsCats['!autofilter'] = { ref: `A1:C${lastCatRow}` }
  wsCats['!freeze'] = { xSplit: 0, ySplit: 1 }
  wsCats['!cols'] = [{ wch: 6 }, { wch: 44 }, { wch: 52 }]
  wsCats['!rows'] = [{ hpt: 28 }, ...finalCatRows.map(() => ({ hpt: 21 }))]

  ;['A', 'B', 'C'].forEach((col) => {
    const ref = `${col}1`
    if (wsCats[ref]) {
      wsCats[ref].s = {
        fill: { fgColor: { rgb: '0F172A' } },
        font: { bold: true, color: { rgb: 'FFFFFF' }, sz: 11 },
        alignment: { vertical: 'center', horizontal: 'left' },
        border: headerBorder
      }
    }
  })

  for (let r = 2; r <= lastCatRow; r++) {
    const isEven = r % 2 === 0
    ;['A', 'B', 'C'].forEach((col, idx) => {
      const ref = `${col}${r}`
      if (!wsCats[ref]) wsCats[ref] = { t: 's', v: '' }
      wsCats[ref].s = {
        fill: { fgColor: { rgb: isEven ? 'E0F2FE' : 'FFFFFF' } },
        font: { color: { rgb: '0F172A' }, sz: 10.5 },
        border: borderThin,
        alignment: { vertical: 'center', horizontal: idx === 0 ? 'center' : 'left' }
      }
    })
  }

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, wsProducts, 'Новые товары')
  XLSX.utils.book_append_sheet(wb, wsCats, 'Справочник категорий')

  const today = new Date().toISOString().slice(0, 10)
  await saveWorkbookCrossPlatform(wb, `Template_New_Products_${today}.xlsx`)
}


const handleCreateFileChange = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  emit('error', '')
  createFileName.value = file.name
  parsedCreateRows.value = []

  try {
    const buffer = await file.arrayBuffer()
    const wb = XLSX.read(buffer, { type: 'array' })
    const firstSheetName = wb.SheetNames[0]
    const ws = wb.Sheets[firstSheetName]
    const rawRows = XLSX.utils.sheet_to_json(ws, { defval: '' })

    const seenInFile = new Set()
    const parsed = []

    for (const r of rawRows) {
      const sku = String(r['Артикул (SKU)*'] ?? r['Артикул'] ?? '').trim()
      const name = String(r['Наименование*'] ?? r['Наименование'] ?? '').trim()
      const groupId = String(r['Группа цвета (groupId)*'] ?? r['Группа цвета (groupId)'] ?? r['Группа цвета'] ?? '').trim()
      const colorName = String(r['Цвет*'] ?? r['Цвет'] ?? '').trim()
      const category = String(r['Категория*'] ?? r['Категория'] ?? '').trim()
      const subcategory = String(r['Подкатегория*'] ?? r['Подкатегория'] ?? '').trim()

      // Пропускаем полностью пустые строки шаблона и строку-образец ПРИМЕР-001
      if (!sku && !name && !groupId && !colorName && !category && !subcategory) continue
      if (sku.toUpperCase() === 'ПРИМЕР-001') continue

      const specs = String(r['Краткие характеристики'] ?? r['Характеристики'] ?? '').trim()
      const description = String(r['Описание'] ?? '').trim()
      const promoLabel = String(r['Акционный бейдж'] ?? '').trim()

      const retailPrice = parseOptionalNumber(r['Розничная цена (BYN)'] ?? r['Розничная цена (BYN)*'] ?? r['Розничная цена']) ?? 0
      const wholesalePrice = parseOptionalNumber(r['Оптовая цена (BYN)'] ?? r['Оптовая цена (BYN)*'] ?? r['Оптовая цена']) ?? 0
      const minWholesaleQty = Math.max(1, parseOptionalInt(r['Мин. партия опт (шт.)']) ?? 5)
      const stock = Math.max(0, parseOptionalInt(r['Начальный остаток (шт.)']) ?? 0)
      const oldRetailPrice = parseOptionalNumber(r['Старая розница (BYN)'])
      const oldWholesalePrice = parseOptionalNumber(r['Старый опт (BYN)'])

      const allowedSubs = categorySubcategoriesMap.value.get(category)

      // Проверяем все 6 обязательных полей + соответствие подкатегории выбранной категории
      let errorReason = ''
      if (!sku) {
        errorReason = 'Не указан артикул'
      } else if (!groupId) {
        errorReason = 'Не указана группа цвета'
      } else if (!colorName) {
        errorReason = 'Не указан цвет'
      } else if (!category) {
        errorReason = 'Не указана категория'
      } else if (categorySubcategoriesMap.value.size > 0 && !allowedSubs) {
        errorReason = `Категория «${category}» не найдена`
      } else if (!subcategory) {
        errorReason = 'Не указана подкатегория'
      } else if (allowedSubs && allowedSubs.size > 0 && !allowedSubs.has(subcategory)) {
        errorReason = `Подкатегория «${subcategory}» не входит в «${category}»`
      } else if (!name) {
        errorReason = 'Не указано наименование'
      } else if (productsBySku.value.has(sku.toLowerCase())) {
        errorReason = 'Артикул уже есть в каталоге'
      } else if (seenInFile.has(sku.toLowerCase())) {
        errorReason = 'Дубликат артикула внутри файла'
      }


      if (sku) seenInFile.add(sku.toLowerCase())

      parsed.push({
        sku,
        groupId,
        colorName,
        category,
        subcategory,
        name,
        specs,
        description,
        retailPrice,
        wholesalePrice,
        minWholesaleQty,
        stock,
        oldRetailPrice,
        oldWholesalePrice,
        promoLabel,
        isValid: !errorReason,
        errorReason
      })
    }

    if (parsed.length === 0) {
      emit('error', 'В файле не найдено новых строк для добавления (строка ПРИМЕР-001 автоматически пропускается).')
      return
    }

    parsedCreateRows.value = parsed
  } catch (err) {
    emit('error', 'Не удалось прочитать Excel-файл. Проверьте формат .xlsx')
  }
}

const validCreateRows = computed(() => parsedCreateRows.value.filter((r) => r.isValid))
const invalidCreateRows = computed(() => parsedCreateRows.value.filter((r) => !r.isValid))

const executeBulkCreate = async () => {
  if (validCreateRows.value.length === 0) return

  isApplyingCreate.value = true
  emit('error', '')

  try {
    const res = await api.adminBulkCreateProducts({
      items: validCreateRows.value.map((r) => ({
        ...r,
        isHidden: createAsHidden.value
      }))
    })
    emit('updated')

    let msg = `Успешно создано карточек товаров: ${res.createdCount} шт.`
    if (createAsHidden.value) {
      msg += ' (скрыты с витрины до добавления фото)'
    }
    if (res.skipped?.length) {
      msg += ` • пропущено: ${res.skipped.length}`
    }
    emit('toast', msg)

    parsedCreateRows.value = []
    createFileName.value = ''
  } catch (err) {
    emit('error', err.message || 'Ошибка при массовом добавлении карточек')
  } finally {
    isApplyingCreate.value = false
  }
}

</script>

<template>
  <div class="tab-content">
    <div class="bulk-mode-switcher">
      <button
        type="button"
        class="bulk-mode-btn"
        :class="{ active: mode === 'update' }"
        @click="mode = 'update'"
      >
        <RefreshCw :size="17" />
        <span>1. Обновление цен и остатков</span>
      </button>

      <button
        type="button"
        class="bulk-mode-btn"
        :class="{ active: mode === 'create' }"
        @click="mode = 'create'"
      >
        <PlusCircle :size="17" />
        <span>2. Добавление новых карточек (без фото)</span>
      </button>
    </div>

    <div v-if="mode === 'update'" class="bulk-panel">
      <div class="bulk-steps-grid">
        <article class="bulk-step-card">
          <div class="step-badge">Шаг 1</div>
          <h2 class="bulk-card-title">Скачайте Excel-шаблон с текущими товарами</h2>
          <p class="bulk-card-desc">
            В шаблон уже выгружены все ваши текущие артикулы, цены и остатки.
            Заполните только те ячейки в колонках <strong>«Новая розничная цена»</strong>,
            <strong>«Новая оптовая цена»</strong> или <strong>«Остаток»</strong>, которые нужно изменить.
            Пустые ячейки останутся без изменений.
          </p>
          <button type="button" class="btn-bulk-secondary" @click="downloadUpdateTemplate">
            <Download :size="17" />
            <span>Скачать шаблон цен и остатков (.xlsx)</span>
          </button>
        </article>

        <article class="bulk-step-card">
          <div class="step-badge">Шаг 2</div>
          <h2 class="bulk-card-title">Выберите правило остатков и загрузите файл</h2>

          <div class="stock-mode-options">
            <label class="stock-radio-card" :class="{ selected: stockMode === 'add' }">
              <input v-model="stockMode" type="radio" value="add" />
              <div>
                <strong>Прибавить к существующим остаткам (+ / −)</strong>
                <span>Например: было 10 шт., в файле 5 → станет 15 шт. (для списания укажите -3).</span>
              </div>
            </label>

            <label class="stock-radio-card danger" :class="{ selected: stockMode === 'replace' }">
              <input v-model="stockMode" type="radio" value="replace" />
              <div>
                <strong>Полностью заменить остатки (=)</strong>
                <span>Перезапишет текущее количество на складе точным числом из таблицы (инвентаризация).</span>
              </div>
            </label>
          </div>

          <input
            ref="updateFileInput"
            type="file"
            accept=".xlsx,.xls"
            hidden
            @change="handleUpdateFileChange"
          />

          <button type="button" class="btn-bulk-primary" @click="updateFileInput?.click()">
            <Upload :size="17" />
            <span>{{ updateFileName ? `Файл: ${updateFileName}` : 'Загрузить заполненный Excel (.xlsx)' }}</span>
          </button>
        </article>
      </div>

      <div v-if="parsedUpdateRows.length > 0" class="bulk-preview-box">
        <div class="preview-header">
          <div>
            <h3>Предпросмотр изменений ({{ updateFileName }})</h3>
            <p>
              Готово к обновлению: <strong>{{ validUpdateRows.length }}</strong> поз.
              <span v-if="missingUpdateRows.length > 0" class="text-danger">
                • Не найдено в базе: <strong>{{ missingUpdateRows.length }}</strong> SKU
              </span>
            </p>
          </div>

          <div class="preview-actions">
            <button
              type="button"
              class="btn-clear-preview"
              @click="parsedUpdateRows = []; updateFileName = ''"
            >
              Сбросить
            </button>

            <button
              type="button"
              class="btn-apply-bulk"
              :class="{ danger: stockMode === 'replace' && stockAffectedCount > 0 }"
              :disabled="validUpdateRows.length === 0 || isApplyingUpdate"
              @click="triggerApplyUpdate"
            >
              <CheckCircle2 :size="17" />
              <span>
                {{
                  isApplyingUpdate
                    ? 'Применение...'
                    : `Применить изменения (${validUpdateRows.length})`
                }}
              </span>
            </button>
          </div>
        </div>

        <div class="preview-search-bar">
          <input
            v-model="previewSearchQuery"
            type="text"
            class="preview-search-input"
            placeholder="Быстрый поиск в таблице по артикулу, названию или цвету..."
          />
        </div>

        <div class="preview-table-wrap">
          <table class="preview-table">
            <thead>
              <tr>
                <th>Артикул</th>
                <th>Товар</th>
                <th>Цвет</th>
                <th>Розница (BYN)</th>
                <th>Опт (BYN)</th>
                <th>Остаток ({{ stockMode === 'add' ? 'прибавление' : 'замена' }})</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, idx) in filteredUpdatePreview"
                :key="idx"
                :class="{ 'row-invalid': !row.found }"
              >
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ row.name }}</td>
                <td>
                  <span v-if="row.colorName" class="color-chip">{{ row.colorName }}</span>
                  <span v-else class="muted-val">—</span>
                </td>
                <td>
                  <template v-if="!row.found">—</template>
                  <template v-else-if="row.retailPrice !== null">
                    <span class="old-val">{{ row.currentRetail.toFixed(2) }}</span> →
                    <strong class="new-val">{{ row.retailPrice.toFixed(2) }}</strong>
                  </template>
                  <span v-else class="muted-val">без изм. ({{ row.currentRetail.toFixed(2) }})</span>
                </td>
                <td>
                  <template v-if="!row.found">—</template>
                  <template v-else-if="row.wholesalePrice !== null">
                    <span class="old-val">{{ row.currentWholesale.toFixed(2) }}</span> →
                    <strong class="new-val">{{ row.wholesalePrice.toFixed(2) }}</strong>
                  </template>
                  <span v-else class="muted-val">без изм. ({{ row.currentWholesale.toFixed(2) }})</span>
                </td>
                <td>
                  <template v-if="!row.found">
                    <span class="badge-err">Не найден</span>
                  </template>
                  <template v-else-if="row.stockValue !== null">
                    <span class="old-val">{{ row.currentStock }}</span> →
                    <strong class="new-val" :class="{ warn: stockMode === 'replace' }">
                      {{ calcPreviewStock(row) }} шт.
                    </strong>
                    <span class="delta-pill">
                      {{
                        stockMode === 'add'
                          ? (row.stockValue >= 0 ? `+${row.stockValue}` : row.stockValue)
                          : 'замена'
                      }}
                    </span>
                  </template>
                  <span v-else class="muted-val">без изм. ({{ row.currentStock }} шт.)</span>
                </td>
              </tr>
            </tbody>
          </table>

        </div>
      </div>
    </div>
    <div v-else class="bulk-panel">
      <div class="bulk-steps-grid">
        <article class="bulk-step-card">
          <div class="step-badge">Шаг 1</div>
          <h2 class="bulk-card-title">Скачайте шаблон для новых товаров</h2>
          <p class="bulk-card-desc">
            В файле есть пример заполнения и второй лист <strong>«Справочник категорий»</strong>,
            откуда удобно копировать точные названия разделов и подкатегорий. Фотографии можно загрузить позже в карточках.
          </p>
          <button type="button" class="btn-bulk-secondary" @click="downloadCreateTemplate">
            <FileSpreadsheet :size="17" />
            <span>Скачать шаблон новых карточек (.xlsx)</span>
          </button>
        </article>


        <article class="bulk-step-card">
          <div class="step-badge">Шаг 2</div>
          <h2 class="bulk-card-title">Загрузите заполненный файл для проверки</h2>
          <p class="bulk-card-desc">
            Система проверит уникальность артикулов (SKU) и наличие указанных категорий перед сохранением в каталог.
          </p>

          <input
            ref="createFileInput"
            type="file"
            accept=".xlsx,.xls"
            hidden
            @change="handleCreateFileChange"
          />

          <button type="button" class="btn-bulk-primary" @click="createFileInput?.click()">
            <Upload :size="17" />
            <span>{{ createFileName ? `Файл: ${createFileName}` : 'Загрузить таблицу новых товаров (.xlsx)' }}</span>
          </button>
        </article>
      </div>

      <div v-if="parsedCreateRows.length > 0" class="bulk-preview-box">
        <div class="preview-header">
          <div>
            <h3>Проверка новых карточек ({{ createFileName }})</h3>
            <p>
              Готово к созданию: <strong>{{ validCreateRows.length }}</strong> шт.
              <span v-if="invalidCreateRows.length > 0" class="text-danger">
                • С ошибками (будут пропущены): <strong>{{ invalidCreateRows.length }}</strong>
              </span>
            </p>
          </div>

          <div class="preview-actions">
            <button
              type="button"
              class="btn-clear-preview"
              @click="parsedCreateRows = []; createFileName = ''"
            >
              Сбросить
            </button>

            <button
              type="button"
              class="btn-apply-bulk"
              :disabled="validCreateRows.length === 0 || isApplyingCreate"
              @click="executeBulkCreate"
            >
              <PlusCircle :size="17" />
              <span>
                {{
                  isApplyingCreate
                    ? 'Создание карточек...'
                    : `Добавить в каталог (${validCreateRows.length})`
                }}
              </span>
            </button>
          </div>
        </div>

        <div class="preview-table-wrap">
          <table class="preview-table">
            <thead>
              <tr>
                <th>Статус</th>
                <th>Артикул</th>
                <th>Категория</th>
                <th>Подкатегория</th>
                <th>Наименование</th>
                <th>Розница / Опт</th>
                <th>Остаток</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, idx) in parsedCreateRows"
                :key="idx"
                :class="{ 'row-invalid': !row.isValid }"
              >
                <td>
                  <span v-if="row.isValid" class="badge-ok">ОК</span>
                  <span v-else class="badge-err">{{ row.errorReason }}</span>
                </td>
                <td><strong>{{ row.sku || '—' }}</strong></td>
                <td>{{ row.category || '—' }}</td>
                <td>{{ row.subcategory || '—' }}</td>
                <td>{{ row.name || '—' }}</td>
                <td>{{ row.retailPrice.toFixed(2) }} / {{ row.wholesalePrice.toFixed(2) }} BYN</td>
                <td>{{ row.stock }} шт.</td>
              </tr>
            </tbody>
          </table>

        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="isReplaceConfirmOpen" class="bulk-modal-backdrop" @click.self="isReplaceConfirmOpen = false">
        <div class="bulk-warning-modal" role="dialog" aria-modal="true">
          <div class="warn-modal-head">
            <div class="warn-circle">
              <AlertTriangle :size="26" color="#dc2626" />
            </div>
            <button type="button" class="btn-close-warn" @click="isReplaceConfirmOpen = false">
              <X :size="18" />
            </button>
          </div>

          <h3 class="warn-modal-title">Подтвердите полную замену остатков!</h3>
          <p class="warn-modal-text">
            Вы выбрали режим <strong>«Полностью заменить остатки»</strong>. Текущие значения остатков на складе
            будут безвозвратно перезаписаны числами из Excel-файла для
            <strong>{{ stockAffectedCount }} поз.</strong>
          </p>

          <div v-if="zeroStockReplaceCount > 0" class="warn-zero-alert">
            Внимание: для <strong>{{ zeroStockReplaceCount }} поз.</strong> остаток будет установлен в <strong>0 шт.</strong> (товары станут недоступны для заказа).
          </div>

          <div class="warn-modal-actions">
            <button type="button" class="btn-warn-cancel" @click="isReplaceConfirmOpen = false">
              Отмена, проверить файл
            </button>
            <button type="button" class="btn-warn-confirm-danger" @click="executeBulkUpdate">
              Да, полностью заменить остатки
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>

</template>


<style scoped>
.bulk-mode-switcher {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.bulk-mode-btn {
  height: 48px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  color: #334155;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.16s ease;
}

.bulk-mode-btn:hover {
  border-color: #0f172a;
}

.bulk-mode-btn.active {
  background-color: #0f172a;
  border-color: #0f172a;
  color: #A3D2F9;
}

.bulk-steps-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.bulk-step-card {
  background-color: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 18px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-badge {
  align-self: flex-start;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 11.5px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 999px;
}

.bulk-card-title {
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
}

.bulk-card-desc {
  font-size: 13.5px;
  color: #475569;
  line-height: 1.5;
}

.stock-mode-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stock-radio-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 11px 13px;
  border-radius: 12px;
  border: 1.5px solid #cbd5e1;
  background-color: #f8fafc;
  cursor: pointer;
  transition: all 0.15s ease;
}

.stock-radio-card input {
  margin-top: 3px;
}

.stock-radio-card strong {
  display: block;
  font-size: 13.5px;
  color: #0f172a;
}

.stock-radio-card span {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.stock-radio-card.selected {
  border-color: #0284c7;
  background-color: #f0f9ff;
}

.stock-radio-card.danger.selected {
  border-color: #dc2626;
  background-color: #fef2f2;
}

.btn-bulk-secondary,
.btn-bulk-primary {
  margin-top: auto;
  height: 44px;
  padding: 0 18px;
  border-radius: 11px;
  font-size: 13.5px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.15s ease;
}

.btn-bulk-secondary {
  border: 1.5px solid #0284c7;
  background-color: #ffffff;
  color: #0284c7;
}

.btn-bulk-secondary:hover {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-bulk-primary {
  border: none;
  background-color: #0f172a;
  color: #A3D2F9;
}

.btn-bulk-primary:hover {
  background-color: #1e293b;
}

.bulk-preview-box {
  margin-top: 20px;
  background-color: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 18px;
  padding: 20px;
}

.preview-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.preview-header h3 {
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
}

.preview-header p {
  font-size: 13px;
  color: #475569;
  margin-top: 2px;
}

.text-danger {
  color: #dc2626;
}

.preview-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-clear-preview {
  height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #f8fafc;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-apply-bulk {
  height: 40px;
  padding: 0 18px;
  border-radius: 10px;
  border: none;
  background-color: #16a34a;
  color: #ffffff;
  font-size: 13.5px;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.btn-apply-bulk.danger {
  background-color: #dc2626;
}

.btn-apply-bulk:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.preview-table-wrap {
  overflow-x: auto;
  max-height: 420px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.preview-table th {
  position: sticky;
  top: 0;
  background-color: #f1f5f9;
  color: #334155;
  text-align: left;
  padding: 10px 12px;
  font-weight: 800;
  border-bottom: 1px solid #cbd5e1;
}

.preview-table td {
  padding: 9px 12px;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

.row-invalid {
  background-color: #fef2f2;
}

.old-val {
  color: #94a3b8;
  text-decoration: line-through;
}

.new-val {
  color: #15803d;
}

.new-val.warn {
  color: #b45309;
}

.muted-val {
  color: #64748b;
  font-size: 12px;
}

.delta-pill {
  margin-left: 6px;
  padding: 2px 7px;
  border-radius: 6px;
  background-color: #e0f2fe;
  color: #0369a1;
  font-size: 11px;
  font-weight: 700;
}

.badge-ok {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background-color: #dcfce7;
  color: #15803d;
  font-weight: 800;
  font-size: 11.5px;
}

.badge-err {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background-color: #fee2e2;
  color: #b91c1c;
  font-weight: 700;
  font-size: 11.5px;
}

/* Предупреждающее модальное окно полной замены остатков */
.bulk-modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 500;
}

.bulk-warning-modal {
  width: 100%;
  max-width: 460px;
  background-color: #ffffff;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.warn-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.warn-circle {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background-color: #fee2e2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close-warn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.warn-modal-title {
  font-size: 19px;
  font-weight: 800;
  color: #0f172a;
}

.warn-modal-text {
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
}

.warn-zero-alert {
  padding: 10px 12px;
  border-radius: 10px;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  font-size: 13px;
}

.warn-modal-actions {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 10px;
  margin-top: 6px;
}

.btn-warn-cancel {
  height: 42px;
  border-radius: 11px;
  border: 1.5px solid #cbd5e1;
  background-color: #f8fafc;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.btn-warn-confirm-danger {
  height: 42px;
  border-radius: 11px;
  border: none;
  background-color: #dc2626;
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.btn-warn-confirm-danger:hover {
  background-color: #b91c1c;
}

@media (max-width: 820px) {
  .bulk-mode-switcher,
  .bulk-steps-grid {
    grid-template-columns: 1fr;
  }
}

.preview-search-bar {
  margin-bottom: 12px;
}

.preview-search-input {
  width: 100%;
  height: 38px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #f8fafc;
  font-size: 13.5px;
  color: #0f172a;
}

.preview-search-input:focus {
  outline: none;
  border-color: #0284c7;
  background-color: #ffffff;
}

.color-chip {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  background-color: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

</style>
