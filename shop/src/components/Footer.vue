<script setup>
const emit = defineEmits(['select-category', 'open-auth', 'open-cart'])

const currentYear = new Date().getFullYear()

const scrollToCatalog = (category = '') => {
  emit('select-category', category)
  const el = document.getElementById('catalog')
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>

<template>
  <footer class="site-footer">
    <div class="footer-container">
      <div class="footer-grid">
        
        <!-- Колонка 1: Бренд и краткое описание -->
        <div class="footer-col">
          <div class="footer-brand">
            <div class="footer-logo">LOGO</div>
            <span class="brand-title">Сандрин<span class="brand-accent">Тайм</span></span>
          </div>
          <p class="footer-about">
            Оптово-розничная продажа наручных, настенных, настольных и умных часов с доставкой по всей Республике Беларусь.
          </p>
          <div class="delivery-badge">
            <span>📦 Отправка через <strong>Европочту</strong> по РБ</span>
            <span>🏪 Самовывоз: <strong>рынок «ЭКСПОБЕЛ»</strong></span>
          </div>
        </div>

        <!-- Колонка 2: Разделы каталога -->
        <div class="footer-col">
          <h3 class="footer-heading">Каталог</h3>
          <ul class="footer-links">
            <li><a href="#catalog" @click.prevent="scrollToCatalog('')">Все модели часов</a></li>
            <li><a href="#catalog" @click.prevent="scrollToCatalog('Наручные часы')">Наручные часы</a></li>
            <li><a href="#catalog" @click.prevent="scrollToCatalog('Интерьерные и настенные')">Интерьерные и настенные</a></li>
            <li><a href="#catalog" @click.prevent="scrollToCatalog('Умные часы и браслеты')">Умные часы и браслеты</a></li>
            <li><a href="#catalog" @click.prevent="scrollToCatalog('Оптовые подборки и боксы')">Оптовые подборки и боксы</a></li>
          </ul>
        </div>

        <!-- Колонка 3: Покупателям и оптовикам -->
        <div class="footer-col">
          <h3 class="footer-heading">Покупателям</h3>
          <ul class="footer-links">
            <li><button type="button" class="footer-link-btn" @click="emit('open-auth', 'register')">Регистрация юрлица / ИП (по УНП)</button></li>
            <li><button type="button" class="footer-link-btn" @click="emit('open-auth', 'login')">Вход в личный кабинет</button></li>
            <li><button type="button" class="footer-link-btn" @click="emit('open-cart')">Корзина и оформление заявки</button></li>
            <li class="info-note">Оплата при получении в отделении Европочты (по паспорту) или на точке самовывоза.</li>
          </ul>
        </div>

        <!-- Колонка 4: Фактический адрес самовывоза и контакты -->
        <div class="footer-col">
          <h3 class="footer-heading">Пункт самовывоза и контакты</h3>
          <ul class="contact-list">
            <li>
              <span class="contact-label">Место самовывоза (торговый павильон):</span>
              <span class="contact-value">Рынок «ЭКСПОБЕЛ», пав. 218/219, 1 этаж, 4 ряд</span>
            </li>
            <li>
              <span class="contact-label">Телефоны менеджеров:</span>
              <a href="tel:+375299891024" class="contact-link">+375 (29) 989-10-24 — Александра</a>
              <a href="tel:+375292560961" class="contact-link">+375 (29) 256-09-61 — Светлана</a>
            </li>
            <li>
              <span class="contact-label">Электронная почта:</span>
              <a href="mailto:vatava67@mail.ru" class="contact-link">vatava67@mail.ru</a>
            </li>
          </ul>
        </div>

      </div>

      <!-- Нижняя полоса с юридическим адресом и реквизитами -->
      <div class="footer-bottom">
        <div class="legal-info">
          <p>
            <strong>Общество с ограниченной ответственностью «Сандринтайм»</strong> (ООО «Сандринтайм») • 
            УНП <strong>690876665</strong>
          </p>
          <p>
            Юридический адрес: Республика Беларусь, Минская область, Логойский район, г. Логойск, ул. Победы, дом 21, пом. 53. 
            Зарегистрировано 03.11.2025 (ИМНС по Логойскому району).
          </p>
          <p>
            Фактический адрес (самовывоз): рынок «ЭКСПОБЕЛ», пав. 218/219, 1 этаж, 4 ряд.
          </p>
        </div>
        <div class="copyright">
          © {{ currentYear }} ООО «Сандринтайм». Все права защищены.
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  width: 100%;
  background-color: #0f172a;
  color: #cbd5e1;
  border-top: 1px solid rgba(163, 210, 249, 0.25);
  margin-top: auto;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 40px 32px 24px;
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.3fr 0.9fr 1fr 1.3fr;
  gap: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid #1e293b;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-logo {
  width: 38px;
  height: 38px;
  border: 2px dashed #A3D2F9;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: #A3D2F9;
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
  color: #ffffff;
}

.brand-accent {
  color: #f59e0b;
}

.footer-about {
  font-size: 13px;
  line-height: 1.55;
  color: #94a3b8;
}

.delivery-badge {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 12px;
  background-color: #1e293b;
  border: 1px solid rgba(163, 210, 249, 0.2);
  font-size: 12px;
  color: #e2e8f0;
}

.delivery-badge strong {
  color: #A3D2F9;
}

.footer-heading {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 2px;
}

.footer-links {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.footer-links a,
.footer-link-btn {
  color: #cbd5e1;
  text-decoration: none;
  font-size: 13px;
  background: transparent;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s ease;
}

.footer-links a:hover,
.footer-link-btn:hover {
  color: #A3D2F9;
}

.info-note {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.45;
  margin-top: 4px;
}

.contact-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.contact-list li {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.contact-label {
  font-size: 11px;
  color: #94a3b8;
}

.contact-value {
  font-size: 13px;
  color: #f8fafc;
  font-weight: 600;
  line-height: 1.4;
}

.contact-link {
  font-size: 13px;
  font-weight: 700;
  color: #A3D2F9;
  text-decoration: none;
}

.contact-link:hover {
  text-decoration: underline;
}

/* Нижний юридический блок */
.footer-bottom {
  padding-top: 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.legal-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.45;
  max-width: 880px;
}

.legal-info strong {
  color: #e2e8f0;
}

.copyright {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

/* Адаптация под планшеты */
@media (max-width: 1024px) {
  .footer-grid {
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
}

/* Адаптация под смартфоны */
@media (max-width: 640px) {
  .footer-container {
    padding: 28px 16px 20px;
  }

  .footer-grid {
    grid-template-columns: 1fr;
    gap: 22px;
  }

  .footer-bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
