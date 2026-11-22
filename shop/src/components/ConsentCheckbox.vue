<script setup>
import { ref } from 'vue'
import { X, ShieldCheck } from 'lucide-vue-next'
import { useBackdropClose } from '../composables/useBackdropClose.js'

defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isPolicyOpen = ref(false)
const { onBackdropMouseDown, onBackdropMouseUp } = useBackdropClose(() => {
  isPolicyOpen.value = false
})
</script>

<template>
  <div class="consent-wrapper">
    <label class="consent-label">
      <input
        type="checkbox"
        :checked="modelValue"
        class="consent-input"
        @change="emit('update:modelValue', $event.target.checked)"
      />
      <span class="consent-text">
        Я даю согласие на
        <button type="button" class="policy-link-btn" @click.stop.prevent="isPolicyOpen = true">
          обработку персональных данных
        </button>
        в соответствии с Законом Республики Беларусь № 99-З.
      </span>
    </label>

    <!-- Модальное окно просмотра политики -->
    <Teleport to="body">
      <div
        v-if="isPolicyOpen"
        class="policy-backdrop"
        @mousedown.self="onBackdropMouseDown"
        @mouseup.self="onBackdropMouseUp"
      >
        <div class="policy-modal" role="dialog" aria-modal="true" aria-label="Политика обработки персональных данных">
          <div class="policy-header">
            <div class="policy-title-wrap">
              <ShieldCheck :size="20" color="#A3D2F9" />
              <h3>Политика обработки персональных данных</h3>
            </div>
            <button type="button" class="policy-close" @click="isPolicyOpen = false" aria-label="Закрыть">
              <X :size="18" />
            </button>
          </div>

          <div class="policy-body">
            <p>
              <strong>1. Общие положения</strong><br />
              Настоящая Политика разработана во исполнение требований Закона Республики Беларусь от 07.05.2021 № 99-З
              «О защите персональных данных» и определяет порядок обработки и защиты персональных данных пользователей
              интернет-магазина <strong>«СандринТайм» (ООО «Сандринтайм», УНП 690876665)</strong>.
            </p>
            <p>
              <strong>2. Цели обработки персональных данных</strong><br />
              — регистрация и идентификация пользователя на сайте (розничного покупателя или представителя юридического лица / ИП);<br />
              — оформление, обработка, комплектация и доставка заказов (в том числе через РУП «Белпочта» / ООО «Европочта» и при самовывозе);<br />
              — обратная связь с покупателем по вопросам статуса заявки, расчёта доставки и гарантийного обслуживания.
            </p>
            <p>
              <strong>3. Перечень обрабатываемых данных</strong><br />
              Фамилия, имя, отчество; контактный номер телефона; адрес электронной почты (Email); город и адрес отделения
              доставки; для юридических лиц и ИП — наименование организации, УНП и юридический адрес.
            </p>
            <p>
              <strong>4. Срок хранения и права субъекта</strong><br />
              Согласие действует до момента достижения целей обработки либо до его отзыва пользователем. Вы вправе в любое
              время отозвать согласие, потребовать изменения или удаления своих персональных данных, направив обращение на
              электронную почту оператора или по контактным телефонам ООО «Сандринтайм».
            </p>
          </div>

          <div class="policy-footer">
            <button
              type="button"
              class="btn-accept-policy"
              @click="emit('update:modelValue', true); isPolicyOpen = false"
            >
              Принять и закрыть
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.consent-wrapper {
  margin-top: 2px;
}

.consent-label {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  cursor: pointer;
  user-select: none;
}

.consent-input {
  width: 17px;
  height: 17px;
  margin-top: 2px;
  accent-color: #0284c7;
  cursor: pointer;
  flex-shrink: 0;
}

.consent-text {
  font-size: 12px;
  line-height: 1.4;
  color: #475569;
}

.policy-link-btn {
  border: none;
  background: transparent;
  padding: 0;
  color: #0284c7;
  font-size: 12px;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
}

.policy-link-btn:hover {
  color: #0f172a;
}

.policy-backdrop {
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

.policy-modal {
  width: 100%;
  max-width: 560px;
  max-height: 85vh;
  background-color: #ffffff;
  border-radius: 18px;
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #0f172a;
}

.policy-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 15px 20px;
  background-color: #0f172a;
  color: #ffffff;
}

.policy-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.policy-title-wrap h3 {
  font-size: 16px;
  font-weight: 800;
}

.policy-close {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.policy-body {
  padding: 18px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-size: 13px;
  line-height: 1.55;
  color: #334155;
}

.policy-footer {
  padding: 12px 20px;
  border-top: 1px solid #e2e8f0;
  background-color: #f8fafc;
  display: flex;
  justify-content: flex-end;
}

.btn-accept-policy {
  height: 38px;
  padding: 0 18px;
  border: none;
  border-radius: 10px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
}

.btn-accept-policy:hover {
  background-color: #7cc0f8;
}
</style>
