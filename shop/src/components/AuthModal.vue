<script setup>
import { ref, reactive, watch } from 'vue'
import { api } from '../services/api.js'
import { ShoppingBag, Building2, X } from 'lucide-vue-next'
import { useBackdropClose } from '../composables/useBackdropClose.js'


const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialMode: {
    type: String,
    default: 'login'
  }
})

const emit = defineEmits(['close', 'success'])
const { onBackdropMouseDown, onBackdropMouseUp } = useBackdropClose(() => emit('close'))


const mode = ref(props.initialMode)
const accountType = ref('retail')
const isLoading = ref(false)
const errorMessage = ref('')

watch(
  () => props.initialMode,
  (newVal) => {
    mode.value = newVal
    errorMessage.value = ''
  }
)

watch(
  () => props.isOpen,
  (opened) => {
    if (opened) {
      errorMessage.value = ''
    }
  }
)

const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  fullName: '',
  phone: '',
  unp: '',
  companyName: '',
  legalAddress: ''
})


const isCheckingUnp = ref(false)
const unpStatusMessage = ref('')
const isUnpVerified = ref(false)

const onUnpInput = (event) => {
  const digitsOnly = event.target.value.replace(/[^0-9]/g, '').slice(0, 9)
  form.unp = digitsOnly
  event.target.value = digitsOnly
}

const switchMode = (newMode) => {
  mode.value = newMode
  errorMessage.value = ''
}

const handleSubmit = async () => {
  errorMessage.value = ''

  if (mode.value === 'register') {
    if (form.password.length < 6) {
      errorMessage.value = 'Пароль должен содержать минимум 6 символов'
      return
    }
    if (form.password !== form.confirmPassword) {
      errorMessage.value = 'Введённые пароли не совпадают'
      return
    }
  }

  if (mode.value === 'register' && accountType.value === 'wholesale') {
    const cleanUnp = form.unp.replace(/[^0-9]/g, '')
    if (cleanUnp.length !== 9) {
      errorMessage.value = 'УНП для Республики Беларусь должен состоять ровно из 9 цифр'
      return
    }
    if (!form.companyName.trim()) {
      errorMessage.value = 'Укажите наименование организации или ИП'
      return
    }
  }

  isLoading.value = true
  try {
    let userData

    if (mode.value === 'login') {
      userData = await api.login({
        email: form.email.trim(),
        password: form.password
      })
    } else {
      userData = await api.register({
        role: accountType.value,
        email: form.email.trim(),
        password: form.password,
        full_name: form.fullName.trim(),
        phone: form.phone.trim(),
        ...(accountType.value === 'wholesale' && {
          unp: form.unp.replace(/[^0-9]/g, ''),
          company_name: form.companyName.trim(),
          legal_address: form.legalAddress.trim()
        })
      })
    }

    emit('success', {
      mode: mode.value,
      user: userData.user,
      token: userData.access_token
    })
    emit('close')
  } catch (err) {
    errorMessage.value = err.message || 'Ошибка соединения с сервером'
  } finally {
    isLoading.value = false
  }
}


</script>


<template>
  <Transition name="fade">
    <div
      v-if="isOpen"
      class="modal-backdrop"
      @mousedown.self="onBackdropMouseDown"
      @mouseup.self="onBackdropMouseUp"
    >

      <div class="modal-card" role="dialog" aria-modal="true" aria-label="Вход и регистрация">
        
        <!-- Шапка окна с рабочей кнопкой закрытия -->
        <div class="modal-header">
          <div class="modal-brand">
            <span class="brand-title">Сандрин<span class="brand-accent">Тайм</span></span>
          </div>
          <button type="button" class="close-btn" @click="emit('close')" aria-label="Закрыть окно">
            <X :size="18" />
          </button>

        </div>

        <!-- Вкладки Вход / Регистрация -->
        <div class="auth-tabs">
          <button 
            type="button" 
            class="tab-btn" 
            :class="{ active: mode === 'login' }" 
            @click="switchMode('login')"
          >
            Вход в аккаунт
          </button>
          <button 
            type="button" 
            class="tab-btn" 
            :class="{ active: mode === 'register' }" 
            @click="switchMode('register')"
          >
            Регистрация
          </button>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit">
          
          <!-- Выбор типа покупателя (только при регистрации) -->
          <div v-if="mode === 'register'" class="account-type-block">
            <label class="block-label">Тип покупателя:</label>
            <div class="type-cards">
              <button 
                type="button" 
                class="type-card" 
                :class="{ selected: accountType === 'retail' }"
                @click="accountType = 'retail'"
              >
                <span class="type-icon"><ShoppingBag :size="20" color="#0284c7" /></span>
                <div class="type-info">
                  <strong>Физлицо</strong>
                  <span>Розничные покупки</span>
                </div>
              </button>

              <button 
                type="button" 
                class="type-card" 
                :class="{ selected: accountType === 'wholesale' }"
                @click="accountType = 'wholesale'"
              >
                <span class="type-icon"><Building2 :size="20" color="#0f172a" /></span>
                <div class="type-info">
                  <strong>Юрлицо / ИП</strong>
                  <span>Оптовые цены по УНП</span>
                </div>
              </button>

            </div>
          </div>

          <!-- Поля для Юрлица / ИП (УНП и наименование) -->
          <!-- Поля для Юрлица / ИП (УНП и наименование) -->
          <div v-if="mode === 'register' && accountType === 'wholesale'" class="wholesale-fields">
            <div class="field-group">
              <label>УНП организации или ИП *</label>
              <input 
                :value="form.unp" 
                @input="onUnpInput" 
                type="text" 
                inputmode="numeric"
                maxlength="9"
                placeholder="690876665" 
                required 
              />
              <span class="unp-counter" :class="{ valid: form.unp.length === 9 }">
                Введено цифр: {{ form.unp.length }} из 9
              </span>
            </div>

            <div class="field-group">
              <label>Наименование организации / ИП *</label>
              <input 
                v-model="form.companyName" 
                type="text" 
                placeholder="ООО «Сандринтайм»" 
                required 
              />
            </div>
          </div>


          <!-- Поля ФИО и телефона (при регистрации) -->
          <template v-if="mode === 'register'">
            <div class="field-group">
              <label>Контактное лицо (ФИО) *</label>
              <input v-model="form.fullName" type="text" placeholder="Иванов Иван Иванович" required />
            </div>

            <div class="field-group">
              <label>Телефон *</label>
              <input v-model="form.phone" type="tel" placeholder="+375 (29) 123-45-67" required />
            </div>
          </template>

          <!-- Email и Пароль -->
          <div class="field-group">
            <label>Электронная почта (Email) *</label>
            <input v-model="form.email" type="email" placeholder="name@example.by" required />
          </div>

          <div class="field-group">
            <label>Пароль *</label>
            <input v-model="form.password" type="password" placeholder="Минимум 6 символов" required />
          </div>

          <div v-if="mode === 'register'" class="field-group">
            <label>Повторите пароль *</label>
            <input v-model="form.confirmPassword" type="password" placeholder="Введите пароль ещё раз" required />
          </div>

          <div v-if="errorMessage" class="error-banner">
            {{ errorMessage }}
          </div>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            <span v-if="isLoading">Подождите...</span>
            <span v-else-if="mode === 'login'">Войти</span>
            <span v-else>{{ accountType === 'wholesale' ? 'Отправить заявку на опт' : 'Зарегистрироваться' }}</span>
          </button>

          <p v-if="mode === 'register' && accountType === 'wholesale'" class="bottom-hint">
            Заявка с реквизитами будет проверена менеджером, после чего для аккаунта откроются оптовые цены.
          </p>
        </form>

      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.68);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 350;
  overflow-y: auto;
}

.modal-card {
  width: 100%;
  max-width: 480px;
  max-height: 92vh;
  background-color: #ffffff;
  border-radius: 20px;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.35);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  color: #0f172a;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  background-color: #0f172a;
  color: #ffffff;
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
}

.brand-accent {
  color: #f59e0b;
}

.close-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  background: transparent;
  color: #ffffff;
  font-size: 16px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.14);
}

.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 16px 22px 0;
  gap: 8px;
}

.tab-btn {
  height: 40px;
  border: none;
  border-bottom: 2px solid #e2e8f0;
  background: transparent;
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  color: #0f172a;
  border-bottom-color: #0284c7;
  background-color: rgba(163, 210, 249, 0.18);
  border-radius: 10px 10px 0 0;
}

.auth-form {
  padding: 16px 22px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.account-type-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.block-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.type-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.type-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  background-color: #f8fafc;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.type-card:hover {
  border-color: #A3D2F9;
}

.type-card.selected {
  border-color: #0284c7;
  background-color: rgba(163, 210, 249, 0.28);
}

.type-icon {
  font-size: 20px;
}

.type-info {
  display: flex;
  flex-direction: column;
}

.type-info strong {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.type-info span {
  font-size: 11px;
  color: #64748b;
}

.wholesale-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background-color: rgba(163, 210, 249, 0.22);
  border: 1px solid #A3D2F9;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0; /* Запрещает сжатие полей */
}

.field-group label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.field-group input {
  height: 42px;
  padding: 0 12px;
  border-radius: 10px;
  border: 1.5px solid #cbd5e1;
  background-color: #ffffff;
  font-size: 14px;
  color: #0f172a;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.field-group input:focus {
  border-color: #0284c7;
  box-shadow: 0 0 0 3px rgba(163, 210, 249, 0.4);
}

.unp-counter {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.unp-counter.valid {
  color: #16a34a;
}

.error-banner {
  padding: 10px 12px;
  border-radius: 10px;
  background-color: #fee2e2;
  color: #b91c1c;
  font-size: 13px;
  font-weight: 600;
}

.submit-btn {
  margin-top: 4px;
  min-height: 46px;
  height: 46px;
  flex-shrink: 0; /* Запрещает сжатие кнопки по высоте */
  width: 100%;
  border: none;
  border-radius: 12px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease;
}

.submit-btn:hover:not(:disabled) {
  background-color: #7cc0f8;
}

.submit-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.bottom-hint {
  font-size: 12px;
  color: #64748b;
  text-align: center;
  line-height: 1.4;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.22s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 480px) {
  .type-cards {
    grid-template-columns: 1fr;
  }
}
</style>
