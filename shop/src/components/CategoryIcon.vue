<script setup>
import { computed } from 'vue'
import {
  Watch,
  Clock,
  AlarmClock,
  Thermometer,
  Radio,
  BatteryCharging,
  Sparkles,
  LayoutGrid,
  Cpu,
  Gift
} from 'lucide-vue-next'

const props = defineProps({
  icon: {
    type: String,
    default: ''
  },
  size: {
    type: [Number, String],
    default: 18
  }
})

// Маппинг строковых ключей и старых эмодзи из БД на SVG-компоненты Lucide
const iconMap = {
  // Ключи для новых/обновлённых категорий
  watch: Watch,
  clock: Clock,
  alarm: AlarmClock,
  weather: Thermometer,
  electronics: Cpu,
  radio: Radio,
  accessories: BatteryCharging,
  gift: Gift,
  all: LayoutGrid,

  // Обратная совместимость с эмодзи из текущей БД
  '⌚': Watch,
  '🕰️': Clock,
  '🕰': Clock,
  '⏰': AlarmClock,
  '⏱️': AlarmClock,
  '🌡️': Thermometer,
  '🌡': Thermometer,
  '⛅': Thermometer,
  '📻': Radio,
  '🔋': BatteryCharging,
  '🔌': Cpu,
  '🎁': Gift,
  '✨': Sparkles,
  '📋': LayoutGrid
}

const resolvedComponent = computed(() => {
  const key = (props.icon || '').trim()
  return iconMap[key] || Watch
})
</script>

<template>
  <component
    :is="resolvedComponent"
    :size="Number(size)"
    :stroke-width="2"
    class="category-svg-icon"
  />
</template>

<style scoped>
.category-svg-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
