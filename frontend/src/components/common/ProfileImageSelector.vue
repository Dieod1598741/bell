<template>
  <Transition name="slide-up">
    <div v-if="visible" class="image-selector-overlay" @click.self="handleClose">
      <div class="image-selector-layer" @click.stop>
        <div class="image-selector-content">
          <!-- 드래그 핸들 -->
          <div class="drag-handle" @click="handleClose">
            <div class="handle-line"></div>
          </div>
          
          <!-- 이미지 선택 -->
          <div class="section">
            <h4 class="section-title">프로필 이미지 선택</h4>
            <div class="image-grid">
              <div
                v-for="(icon, index) in availableIcons"
                :key="index"
                class="image-item"
                :class="{ selected: selectedIcon === icon }"
                @click="handleIconClick(icon)"
              >
                <img :src="icon" :alt="`icon${index + 1}`" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  currentImage: {
    type: String,
    default: ''
  },
  triggerElement: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 사용 가능한 아이콘 목록 생성
const availableIcons = computed(() => {
  const icons = []
  for (let i = 1; i <= 40; i++) {
    icons.push(`/icon/icon${i}.svg`)
  }
  return icons
})

const selectedIcon = ref(props.currentImage || '/icon/icon1.svg')

// props가 변경될 때 선택값 업데이트
watch(() => props.currentImage, (newVal) => {
  if (newVal) {
    selectedIcon.value = newVal
  }
})

const handleIconClick = (icon) => {
  selectedIcon.value = icon
  emit('select', icon)
  visible.value = false
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.image-selector-overlay {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 450px;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-selector-layer {
  width: 100%;
  background: transparent;
  border-radius: 20px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
  margin: 20px;
}

.drag-handle {
  padding: 12px 0 8px;
  display: flex;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.handle-line {
  width: 40px;
  height: 4px;
  background: #d1d5db;
  border-radius: 2px;
}

.image-selector-content {
  overflow-y: auto;
  padding: 20px;
  background: white;
  border-radius: 12px;
  width: 100%;
  min-height: fit-content;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  padding: 8px;
}

.image-item {
  aspect-ratio: 1;
  width: 100%;
  border: 2px solid #e5e7eb;
  border-radius: 50%;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.2s;
  background: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.image-item:hover {
  border-color: #409EFF;
  transform: scale(1.1);
}

.image-item.selected {
  border-color: #409EFF;
  border-width: 3px;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 애니메이션 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: opacity 0.3s ease;
}

.slide-up-enter-active .image-selector-layer,
.slide-up-leave-active .image-selector-layer {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
}

.slide-up-enter-from .image-selector-layer {
  transform: translateY(-20px);
  opacity: 0;
}

.slide-up-enter-to {
  opacity: 1;
}

.slide-up-enter-to .image-selector-layer {
  transform: translateY(0);
  opacity: 1;
}

.slide-up-leave-from {
  opacity: 1;
}

.slide-up-leave-from .image-selector-layer {
  transform: translateY(0);
  opacity: 1;
}

.slide-up-leave-to {
  opacity: 0;
}

.slide-up-leave-to .image-selector-layer {
  transform: translateY(-20px);
  opacity: 0;
}
</style>
