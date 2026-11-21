<script setup>
import { computed } from 'vue'
import { resolveImageUrl } from '../services/api.js'

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  },
  products: {
    type: Array,
    default: () => []
  },
  currentUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'go-catalog',
  'select-category',
  'open-auth',
  'open-account',
  'select-product'
])

const userRole = computed(() => props.currentUser?.role || 'retail')

const featuredProducts = computed(() => {
  const inStock = props.products.filter((p) => (p.stock ?? 0) > 0)
  return (inStock.length > 0 ? inStock : props.products).slice(0, 4)
})

const formatPrice = (value) => {
  return Number(value || 0).toFixed(2).replace('.', ',')
}
</script>

<template>
  <div class="home-page">
    <div class="home-container">
      
      <!-- 1. HERO-БЛОК (Главный экран) -->
      <section class="hero-card">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="pulse-dot"></span>
            <span>Официальный поставщик в Республике Беларусь</span>
          </div>

          <h1 class="hero-title">
            Точность времени и стиль вашего интерьера с <span class="text-accent">СандринТайм</span>
          </h1>

          <p class="hero-description">
            Наручные, настенные и настольные часы, метеостанции и интерьерная электроника 
            для розничных покупателей и бизнеса. Прямые поставки, честная гарантия и удобный 
            онлайн-заказ по всей Беларуси.
          </p>

          <div class="hero-actions">
            <button
              type="button"
              class="btn-primary-hero"
              @click="emit('go-catalog')"
            >
              <span>Перейти в каталог</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </button>

            <button
              v-if="!currentUser"
              type="button"
              class="btn-secondary-hero"
              @click="emit('open-auth', 'register')"
            >
              🏢 Оптовым клиентам (по УНП)
            </button>

            <button
              v-else
              type="button"
              class="btn-secondary-hero"
              @click="emit('open-account')"
            >
              👤 Личный кабинет и заявки
            </button>
          </div>

          <div class="hero-metrics">
            <div class="metric-item">
              <span class="metric-value">{{ products.length || '100+' }}</span>
              <span class="metric-label">моделей в ассортименте</span>
            </div>
            <div class="metric-divider"></div>
            <div class="metric-item">
              <span class="metric-value">100%</span>
              <span class="metric-label">официальная работа (ООО)</span>
            </div>
            <div class="metric-divider"></div>
            <div class="metric-item">
              <span class="metric-value">РБ</span>
              <span class="metric-label">доставка Европочтой и самовывоз</span>
            </div>
          </div>
        </div>

        <!-- Декоративный визуальный блок справа -->
        <div class="hero-visual">
          <div class="clock-showcase">
            <div class="clock-ring outer"></div>
            <div class="clock-ring inner"></div>
            <div class="clock-center-card">
              <div class="clock-emoji">⌚</div>
              <div class="clock-brand">SANDRIN<span class="gold">TIME</span></div>
              <div class="clock-sub">Розница и Опт • B2C / B2B</div>
              <div class="clock-tags">
                <span>Кварц и механика</span>
                <span>Интерьерные</span>
                <span>Смарт-часы</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 2. КАТЕГОРИИ ТОВАРОВ -->
      <section v-if="categories.length > 0" class="section-block">
        <div class="section-header">
          <div>
            <span class="section-eyebrow">Ассортимент</span>
            <h2 class="section-title">Категории товаров</h2>
          </div>
          <button type="button" class="link-all-btn" @click="emit('go-catalog')">
            Весь каталог →
          </button>
        </div>

        <div class="categories-grid">
          <button
            v-for="cat in categories"
            :key="cat.id"
            type="button"
            class="category-card"
            @click="emit('select-category', { category: cat.name, subcategory: '' })"
          >
            <div class="cat-card-top">
              <span class="cat-card-icon">{{ cat.icon || '⌚' }}</span>
              <span class="cat-card-arrow">↗</span>
            </div>
            <h3 class="cat-card-title">{{ cat.name }}</h3>
            <p v-if="cat.subcategories && cat.subcategories.length" class="cat-card-subs">
              {{ cat.subcategories.slice(0, 3).join(' • ') }}
            </p>
            <p v-else class="cat-card-subs">Смотреть все модели раздела</p>
          </button>
        </div>
      </section>

      <!-- 3. БЛОК «О НАС» И ОСНОВНОЙ ФУНКЦИОНАЛ ПЛАТФОРМЫ -->
      <section class="about-grid">
        <div class="about-card">
          <span class="section-eyebrow dark">О компании</span>
          <h2 class="about-title">ООО «Сандринтайм» — надёжный партнёр в мире часов</h2>
          <p class="about-text">
            Мы специализируемся на поставках наручных часов, настенных и настольных интерьерных 
            моделей, будильников и современной домашней электроники. Наша цель — сделать покупку 
            качественных часов простой и прозрачной как для частного покупателя, так и для 
            торговых сетей и корпоративных заказчиков.
          </p>
          <ul class="about-checklist">
            <li>
              <span class="check-badge">✓</span>
              <span>Только проверенные механизмы и официальная гарантия качества</span>
            </li>
            <li>
              <span class="check-badge">✓</span>
              <span>Актуальные складские остатки и реальные фото каждого артикула</span>
            </li>
            <li>
              <span class="check-badge">✓</span>
              <span>Удобный самовывоз в Минске (ТЦ «ЭКСПОБЕЛ») и отправка по всей стране</span>
            </li>
          </ul>
        </div>

        <!-- Карточки функционала сайта -->
        <div class="features-stack">
          <div class="feature-item">
            <div class="feature-icon blue">🛍️</div>
            <div class="feature-info">
              <h3>Розничным покупателям</h3>
              <p>
                Оформляйте заказ онлайн за пару минут: доставка <strong>Европочтой</strong> с 
                отслеживанием трек-кода в личном кабинете или самовывоз.
              </p>
              <button type="button" class="feature-action-link" @click="emit('go-catalog')">
                Выбрать часы в каталоге →
              </button>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon gold">🏢</div>
            <div class="feature-info">
              <h3>Оптовый кабинет для юрлиц и ИП</h3>
              <p>
                Зарегистрируйтесь с указанием <strong>УНП</strong>, получите доступ к оптовым 
                ценам прямо на сайте и выгружайте актуальный прайс-лист в <strong>Excel (.xlsx)</strong>.
              </p>
              <button
                type="button"
                class="feature-action-link"
                @click="currentUser ? emit('open-account') : emit('open-auth', 'register')"
              >
                {{ currentUser ? 'Перейти в профиль →' : 'Зарегистрировать юрлицо →' }}
              </button>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon slate">📊</div>
            <div class="feature-info">
              <h3>Умная корзина и сметы</h3>
              <p>
                Автоматический контроль минимальной оптовой партии, расчёт итоговой суммы и 
                мгновенная выгрузка вашей корзины или заказа в таблицу Excel.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- 4. ПОПУЛЯРНЫЕ МОДЕЛИ ИЗ КАТАЛОГА -->
      <section v-if="featuredProducts.length > 0" class="section-block">
        <div class="section-header">
          <div>
            <span class="section-eyebrow">Витрина</span>
            <h2 class="section-title">Популярные модели в наличии</h2>
          </div>
          <button type="button" class="link-all-btn" @click="emit('go-catalog')">
            Смотреть все модели →
          </button>
        </div>

        <div class="showcase-grid">
          <article
            v-for="item in featuredProducts"
            :key="item.id"
            class="showcase-card"
            @click="emit('select-product', item)"
          >
            <div class="showcase-img-wrap">
              <span class="showcase-sku">Арт. {{ item.sku }}</span>
              <img
                v-if="item.image"
                :src="resolveImageUrl(item.image)"
                :alt="item.name"
                class="showcase-img"
              />
              <span v-else class="showcase-emoji">{{ item.icon || '⌚' }}</span>
            </div>

            <div class="showcase-body">
              <span class="showcase-cat">{{ item.category }}</span>
              <h3 class="showcase-name">{{ item.name }}</h3>
              <div class="showcase-footer">
                <span class="showcase-price">
                  {{ formatPrice(userRole === 'wholesale' ? item.wholesalePrice : item.retailPrice) }} BYN
                </span>
                <span class="showcase-more">Подробнее →</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <!-- 5. НИЖНИЙ CTA БАННЕР -->
      <section class="cta-banner">
        <div class="cta-text">
          <h2>Готовы подобрать идеальные часы?</h2>
          <p>Перейдите в полный каталог с удобным поиском по артикулу, бренду и категориям.</p>
        </div>
        <button type="button" class="btn-cta-catalog" @click="emit('go-catalog')">
          Открыть полный каталог
        </button>
      </section>

    </div>
  </div>
</template>


<style scoped>
.home-page {
  width: 100%;
  padding: 8px 32px 24px;
}

.home-container {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 1. HERO */
.hero-card {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #0f172a 100%);
  color: #f8fafc;
  border-radius: 24px;
  padding: 44px 48px;
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  align-items: center;
  gap: 36px;
  border: 1px solid rgba(163, 210, 249, 0.3);
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
  position: relative;
  overflow: hidden;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  background-color: rgba(163, 210, 249, 0.14);
  border: 1px solid rgba(163, 210, 249, 0.35);
  color: #A3D2F9;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 18px;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #f59e0b;
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.25);
}

.hero-title {
  font-size: 38px;
  font-weight: 800;
  line-height: 1.18;
  letter-spacing: -0.02em;
  margin-bottom: 16px;
  color: #ffffff;
}

.text-accent {
  color: #A3D2F9;
}

.hero-description {
  font-size: 16px;
  line-height: 1.6;
  color: #cbd5e1;
  max-width: 620px;
  margin-bottom: 28px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 32px;
}

.btn-primary-hero {
  height: 52px;
  padding: 0 28px;
  border-radius: 14px;
  border: none;
  background-color: #A3D2F9;
  color: #0f172a;
  font-size: 16px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(163, 210, 249, 0.3);
  transition: transform 0.15s ease, background-color 0.2s ease;
}

.btn-primary-hero:hover {
  background-color: #7cc0f8;
  transform: translateY(-2px);
}

.btn-secondary-hero {
  height: 52px;
  padding: 0 22px;
  border-radius: 14px;
  border: 1.5px solid rgba(163, 210, 249, 0.45);
  background-color: rgba(255, 255, 255, 0.06);
  color: #f8fafc;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary-hero:hover {
  background-color: rgba(163, 210, 249, 0.16);
  border-color: #A3D2F9;
}

.hero-metrics {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
}

.metric-item {
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 22px;
  font-weight: 800;
  color: #f59e0b;
  line-height: 1.2;
}

.metric-label {
  font-size: 12px;
  color: #94a3b8;
}

.metric-divider {
  width: 1px;
  height: 32px;
  background-color: rgba(148, 163, 184, 0.25);
}

/* Визуальная витрина справа в Hero */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.clock-showcase {
  position: relative;
  width: 300px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clock-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed rgba(163, 210, 249, 0.35);
}

.clock-ring.outer {
  inset: 0;
}

.clock-ring.inner {
  inset: 22px;
  border-style: solid;
  border-color: rgba(245, 158, 11, 0.28);
}

.clock-center-card {
  position: relative;
  z-index: 2;
  width: 230px;
  height: 230px;
  border-radius: 50%;
  background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%);
  border: 2px solid rgba(163, 210, 249, 0.5);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
}

.clock-emoji {
  font-size: 46px;
  margin-bottom: 6px;
}

.clock-brand {
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 1.5px;
  color: #ffffff;
}

.clock-brand .gold {
  color: #f59e0b;
}

.clock-sub {
  font-size: 11px;
  color: #A3D2F9;
  font-weight: 600;
  margin-top: 2px;
  margin-bottom: 10px;
}

.clock-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}

.clock-tags span {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 999px;
  background-color: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
}

/* 2. ОБЩИЕ ЗАГОЛОВКИ СЕКЦИЙ */
.section-block {
  background-color: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(10px);
  border-radius: 22px;
  padding: 28px 30px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.section-eyebrow {
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #0284c7;
  margin-bottom: 4px;
}

.section-eyebrow.dark {
  color: #A3D2F9;
}

.section-title {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
}

.link-all-btn {
  padding: 9px 16px;
  border-radius: 10px;
  border: 1.5px solid #0f172a;
  background-color: transparent;
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}

.link-all-btn:hover {
  background-color: #0f172a;
  color: #A3D2F9;
}

/* Сетка категорий */
.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.category-card {
  text-align: left;
  background-color: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;
}

.category-card:hover {
  border-color: #0f172a;
  background-color: #0f172a;
  color: #ffffff;
  transform: translateY(-3px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.15);
}

.cat-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cat-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background-color: #e0f2fe;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.category-card:hover .cat-card-icon {
  background-color: rgba(163, 210, 249, 0.2);
}

.cat-card-arrow {
  font-size: 18px;
  font-weight: 700;
  color: #94a3b8;
}

.category-card:hover .cat-card-arrow {
  color: #A3D2F9;
}

.cat-card-title {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  margin-top: 4px;
}

.category-card:hover .cat-card-title {
  color: #ffffff;
}

.cat-card-subs {
  font-size: 12.5px;
  color: #64748b;
  line-height: 1.4;
}

.category-card:hover .cat-card-subs {
  color: #cbd5e1;
}

/* 3. О НАС И ФУНКЦИОНАЛ */
.about-grid {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 24px;
}

.about-card {
  background-color: #0f172a;
  color: #f8fafc;
  border-radius: 22px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 16px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.18);
}

.about-title {
  font-size: 26px;
  font-weight: 800;
  line-height: 1.25;
  color: #ffffff;
}

.about-text {
  font-size: 15px;
  line-height: 1.65;
  color: #cbd5e1;
}

.about-checklist {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 6px;
}

.about-checklist li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: #e2e8f0;
}

.check-badge {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background-color: #A3D2F9;
  color: #0f172a;
  font-weight: 900;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.features-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  background-color: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(8px);
  border-radius: 18px;
  padding: 20px 22px;
  border: 1px solid #ffffff;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.feature-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.feature-icon.blue {
  background-color: #e0f2fe;
}

.feature-icon.gold {
  background-color: #fef3c7;
}

.feature-icon.slate {
  background-color: #f1f5f9;
}

.feature-info h3 {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 4px;
}

.feature-info p {
  font-size: 13.5px;
  color: #475569;
  line-height: 1.5;
}

.feature-action-link {
  margin-top: 8px;
  padding: 0;
  border: none;
  background: transparent;
  color: #0284c7;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.feature-action-link:hover {
  text-decoration: underline;
}

/* 4. ВИТРИНА ТОВАРОВ */
.showcase-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.showcase-card {
  background-color: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.showcase-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.12);
}

.showcase-img-wrap {
  position: relative;
  height: 170px;
  background-color: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.showcase-sku {
  position: absolute;
  top: 10px;
  left: 10px;
  background-color: #0f172a;
  color: #f8fafc;
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.showcase-img {
  max-width: 100%;
  max-height: 130px;
  object-fit: contain;
}

.showcase-emoji {
  font-size: 46px;
}

.showcase-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.showcase-cat {
  font-size: 11px;
  font-weight: 700;
  color: #0284c7;
}

.showcase-name {
  font-size: 14px;
font-weight: 700;
color: #0f172a;
line-height: 1.35;
display: -webkit-box;
-webkit-line-clamp: 2;
-webkit-box-orient: vertical;
overflow: hidden;
}
.showcase-footer {
margin-top: auto;
padding-top: 8px;
border-top: 1px solid #f1f5f9;
display: flex;
align-items: center;
justify-content: space-between;
}
.showcase-price {
font-size: 16px;
font-weight: 800;
color: #0f172a;
}
.showcase-more {
font-size: 12px;
font-weight: 700;
color: #0284c7;
}
/* 5. НИЖНИЙ CTA БАННЕР */
.cta-banner {
background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
border-radius: 20px;
padding: 28px 36px;
display: flex;
align-items: center;
justify-content: space-between;
gap: 20px;
color: #ffffff;
border: 1px solid rgba(163, 210, 249, 0.3);
}
.cta-text h2 {
font-size: 22px;
font-weight: 800;
margin-bottom: 4px;
}
.cta-text p {
font-size: 14px;
color: #cbd5e1;
}
.btn-cta-catalog {
height: 48px;
padding: 0 26px;
border-radius: 12px;
border: none;
background-color: #A3D2F9;
color: #0f172a;
font-size: 15px;
font-weight: 800;
cursor: pointer;
white-space: nowrap;
transition: background-color 0.2s ease;
}
.btn-cta-catalog:hover {
background-color: #7cc0f8;
}
/* АДАПТИВНОСТЬ */
@media (max-width: 1024px) {
.hero-card {
grid-template-columns: 1fr;
padding: 32px 28px;
}
.hero-visual {
display: none;
}
.about-grid {
grid-template-columns: 1fr;
}
.showcase-grid {
grid-template-columns: repeat(2, minmax(0, 1fr));
}
}
@media (max-width: 680px) {
.home-page {
padding: 0 10px 16px;
}
.home-container {
gap: 18px;
}
.hero-card {
padding: 24px 18px;
border-radius: 18px;
}
.hero-title {
font-size: 25px;
}
.hero-description {
font-size: 14px;
}
.btn-primary-hero,
.btn-secondary-hero {
width: 100%;
justify-content: center;
}
.metric-divider {
display: none;
}
.section-block {
padding: 18px 14px;
border-radius: 16px;
}
.section-title {
font-size: 19px;
}
.categories-grid {
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
}
.category-card {
padding: 14px;
}
.about-card {
padding: 22px 18px;
}
.about-title {
font-size: 20px;
}
.showcase-grid {
gap: 10px;
}
.cta-banner {
flex-direction: column;
text-align: center;
padding: 22px 18px;
}
.btn-cta-catalog {
width: 100%;
}
}

</style>