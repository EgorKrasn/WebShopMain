<script setup>
import { ref } from 'vue'
import { HardDriveDownload, HardDriveUpload, AlertTriangle, Send, Mail } from 'lucide-vue-next'

import { api } from '../../services/api.js'
import './admin.css'

defineProps({
  categoriesCount: {
    type: Number,
    default: 0
  },
  productsCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['restored', 'toast', 'error'])

const isExportingBackup = ref(false)
const isImportingBackup = ref(false)
const backupFileInput = ref(null)

const handleExportBackup = async () => {
  isExportingBackup.value = true
  emit('error', '')
  try {
    await api.adminExportBackup()
    emit('toast', 'Резервная копия каталога и фото (.zip) успешно скачана')
  } catch (err) {
    emit('error', err.message || 'Ошибка при создании резервной копии')
  } finally {
    isExportingBackup.value = false
  }
}

const triggerBackupFileSelect = () => {
  backupFileInput.value?.click()
}

const handleImportBackupFile = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  const confirmed = confirm(
    `ВНИМАНИЕ! Восстановление из архива «${file.name}» ПОЛНОСТЬЮ ЗАМЕНИТ все текущие категории, товары и загруженные фотографии.\n\nПродолжить восстановление?`
  )
  if (!confirmed) return

  isImportingBackup.value = true
  emit('error', '')
  try {
    const res = await api.adminImportBackup(file)
    emit('restored')
    emit(
      'toast',
      `Каталог восстановлен: категорий — ${res.categoriesCount}, товаров — ${res.productsCount}, фото — ${res.filesCount}`
    )
  } catch (err) {
    emit('error', err.message || 'Не удалось восстановить данные из архива')
  } finally {
    isImportingBackup.value = false
  }
}

const isTestingTelegram = ref(false)
const isTestingEmail = ref(false)

const handleTestTelegram = async () => {
  isTestingTelegram.value = true
  emit('error', '')
  try {
    const res = await api.adminTestTelegram()
    emit('toast', res.message || 'Тестовое уведомление отправлено в Telegram')
  } catch (err) {
    emit('error', err.message || 'Не удалось отправить тестовое сообщение в Telegram')
  } finally {
    isTestingTelegram.value = false
  }
}

const handleTestEmail = async () => {
  isTestingEmail.value = true
  emit('error', '')
  try {
    await api.adminTestEmail()
    emit('toast', 'Тестовое письмо отправлено на Email администратора')
  } catch (err) {
    emit('error', err.message || 'Не удалось отправить тестовое письмо')
  } finally {
    isTestingEmail.value = false
  }
}

</script>

<template>
  <div class="tab-content">
    <div class="backup-grid">
      <article class="backup-card">
        <div class="backup-card-head">
          <div class="hub-icon-box indigo">
            <HardDriveDownload :size="24" :stroke-width="2.1" />
          </div>
          <div>
            <h2 class="backup-title">Создать резервную копию (.zip)</h2>
            <p class="backup-sub">Полная выгрузка каталога для хранения или переноса на другой сервер</p>
          </div>
        </div>

        <ul class="backup-checklist">
          <li>Все категории и подкатегории (включая иконки и порядок сортировки)</li>
          <li>Все карточки товаров, артикулы, характеристики, цены (опт/розница) и остатки</li>
          <li>Все загруженные изображения товаров из папки <code>uploads/</code></li>
        </ul>

        <div class="backup-stats-bar">
          <span>Категорий: <strong>{{ categoriesCount }}</strong></span>
          <span>Товаров: <strong>{{ productsCount }}</strong></span>
        </div>

        <button
          type="button"
          class="btn-backup-export"
          :disabled="isExportingBackup || isImportingBackup"
          @click="handleExportBackup"
        >
          <HardDriveDownload :size="17" />
          <span>{{ isExportingBackup ? 'Формирование архива...' : 'Скачать резервную копию (.zip)' }}</span>
        </button>
      </article>

      <article class="backup-card restore">
        <div class="backup-card-head">
          <div class="hub-icon-box gold">
            <HardDriveUpload :size="24" :stroke-width="2.1" />
          </div>
          <div>
            <h2 class="backup-title">Восстановить из архива (.zip)</h2>
            <p class="backup-sub">Миграция или откат каталога из ранее сохранённой резервной копии</p>
          </div>
        </div>

        <div class="backup-warning-box">
          <AlertTriangle :size="18" class="warn-ico" />
          <div>
            <strong>Внимание: полная замена данных!</strong>
            <p>
              При загрузке архива текущие категории, товары и файлы в папке <code>uploads/</code>
              будут полностью перезаписаны данными из архива. Пользователи и заказы при этом сохраняются.
            </p>
          </div>
        </div>

        <input
          ref="backupFileInput"
          type="file"
          accept=".zip,application/zip"
          hidden
          @change="handleImportBackupFile"
        />

        <button
          type="button"
          class="btn-backup-import"
          :disabled="isImportingBackup || isExportingBackup"
          @click="triggerBackupFileSelect"
        >
          <HardDriveUpload :size="17" />
          <span>{{ isImportingBackup ? 'Восстановление данных...' : 'Выбрать .zip-архив и восстановить' }}</span>
        </button>
      </article>
    </div>

    <article class="backup-card notify-card" style="margin-top: 18px;">
      <div class="backup-card-head">
        <div class="hub-icon-box sky">
          <Send :size="24" :stroke-width="2.1" />
        </div>
        <div>
          <h2 class="backup-title">Проверка уведомлений менеджера (Telegram и Email)</h2>
          <p class="backup-sub">
            Отправка тестового сигнала для проверки ключей <code>TELEGRAM_BOT_TOKEN</code>,
            <code>TELEGRAM_CHAT_ID</code> и SMTP-почты из <code>backend/.env</code>
          </p>
        </div>
      </div>

      <div class="notify-actions-row">
        <button
          type="button"
          class="btn-test-telegram"
          :disabled="isTestingTelegram"
          @click="handleTestTelegram"
        >
          <Send :size="16" />
          <span>{{ isTestingTelegram ? 'Отправка в Telegram...' : 'Тест Telegram-бота' }}</span>
        </button>

        <button
          type="button"
          class="btn-test-email"
          :disabled="isTestingEmail"
          @click="handleTestEmail"
        >
          <Mail :size="16" />
          <span>{{ isTestingEmail ? 'Отправка письма...' : 'Тест Email-уведомлений' }}</span>
        </button>
      </div>
    </article>

  </div>
</template>

<style scoped>
.backup-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.backup-card {
  background-color: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 18px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.backup-card.restore {
  border-color: #fde68a;
  background-color: #fffdf7;
}

.backup-card-head {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.hub-icon-box {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hub-icon-box.gold {
  background-color: #fef3c7;
  color: #d97706;
}

.hub-icon-box.indigo {
  background-color: #e0e7ff;
  color: #4338ca;
}

.backup-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.backup-sub {
  font-size: 13px;
  color: #64748b;
  margin-top: 2px;
}

.backup-checklist {
  margin: 0;
  padding-left: 18px;
  font-size: 13.5px;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.backup-stats-bar {
  display: flex;
  gap: 18px;
  padding: 10px 14px;
  background-color: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  font-size: 13px;
  color: #475569;
}

.backup-warning-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  color: #92400e;
  font-size: 13px;
  line-height: 1.45;
}

.backup-warning-box .warn-ico {
  flex-shrink: 0;
  margin-top: 2px;
}

.backup-warning-box p {
  margin-top: 4px;
}

.btn-backup-export,
.btn-backup-import {
  margin-top: auto;
  height: 44px;
  padding: 0 18px;
  border-radius: 11px;
  border: none;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.15s ease;
}

.btn-backup-export {
  background-color: #0f172a;
  color: #A3D2F9;
}

.btn-backup-import {
  background-color: #d97706;
  color: #ffffff;
}

.btn-backup-export:disabled,
.btn-backup-import:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 820px) {
  .backup-grid {
    grid-template-columns: 1fr;
  }
}

.hub-icon-box.sky {
  background-color: #e0f2fe;
  color: #0284c7;
}

.notify-actions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.btn-test-telegram,
.btn-test-email {
  height: 42px;
  padding: 0 18px;
  border-radius: 11px;
  border: none;
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 0.15s ease, transform 0.1s ease;
}

.btn-test-telegram {
  background-color: #0284c7;
  color: #ffffff;
}

.btn-test-email {
  background-color: #0f172a;
  color: #A3D2F9;
}

.btn-test-telegram:disabled,
.btn-test-email:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

</style>
