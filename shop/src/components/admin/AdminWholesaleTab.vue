<script setup>
import { Clock, CheckCircle2, XCircle } from 'lucide-vue-next'
import './admin.css'

defineProps({
  requests: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['decision'])
</script>

<template>
  <div class="tab-content">
    <div v-if="requests.length === 0" class="empty-box">
      Заявок на подключение оптового аккаунта пока нет.
    </div>

    <div v-else class="cards-grid">
      <article
        v-for="user in requests"
        :key="user.id"
        class="admin-card"
        :class="{ 'is-pending': user.wholesaleStatus === 'pending' }"
      >
        <div class="card-header">
          <div>
            <strong class="company-title">{{ user.companyName || 'Без названия' }}</strong>
            <span class="unp-tag">УНП: {{ user.unp }}</span>
          </div>

          <span v-if="user.wholesaleStatus === 'pending'" class="status-pill pending">
            <Clock :size="13" /> Ожидает проверки
          </span>
          <span v-else-if="user.wholesaleStatus === 'approved'" class="status-pill approved">
            <CheckCircle2 :size="13" /> Опт одобрен
          </span>
          <span v-else class="status-pill rejected">
            <XCircle :size="13" /> Отклонено
          </span>
        </div>

        <div class="card-details">
          <div><strong>Контактное лицо:</strong> {{ user.fullName }}</div>
          <div><strong>Телефон:</strong> {{ user.phone }}</div>
          <div><strong>Email:</strong> {{ user.email }}</div>
          <div v-if="user.legalAddress"><strong>Юр. адрес:</strong> {{ user.legalAddress }}</div>
        </div>

        <div class="card-actions">
          <button
            v-if="user.wholesaleStatus !== 'approved'"
            type="button"
            class="btn-approve"
            @click="emit('decision', { userId: user.id, decision: 'approved' })"
          >
            <CheckCircle2 :size="15" /> Одобрить опт
          </button>
          <button
            v-if="user.wholesaleStatus !== 'rejected'"
            type="button"
            class="btn-reject"
            @click="emit('decision', { userId: user.id, decision: 'rejected' })"
          >
            <XCircle :size="15" /> Отклонить
          </button>
        </div>
      </article>
    </div>
  </div>
</template>
