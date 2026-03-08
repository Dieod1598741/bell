<template>
  <Transition name="slide-up">
    <div v-if="visible" class="action-layer-overlay" @click.self="handleClose">
      <div class="action-layer" @click.stop>
        <!-- 컨텐츠 -->
        <div class="action-layer-content">
          <!-- 드래그 핸들 -->
          <div class="drag-handle" @click="handleClose">
            <div class="handle-line"></div>
          </div>
          <slot />
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'close'])

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

const handleKeyDown = (event) => {
  if (event.key === 'Escape' && props.visible) {
    handleClose()
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    document.addEventListener('keydown', handleKeyDown)
  } else {
    document.removeEventListener('keydown', handleKeyDown)
  }
})

onMounted(() => {
  if (props.visible) {
    document.addEventListener('keydown', handleKeyDown)
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.action-layer-overlay {
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

.action-layer {
  width: 100%;
  background: transparent;
  border-radius: 30px;
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

.action-layer-content {
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

/* 애니메이션 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: opacity 0.3s ease;
}

.slide-up-enter-active .action-layer,
.slide-up-leave-active .action-layer {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
}

.slide-up-enter-from .action-layer {
  transform: translateY(-20px);
  opacity: 0;
}

.slide-up-enter-to {
  opacity: 1;
}

.slide-up-enter-to .action-layer {
  transform: translateY(0);
  opacity: 1;
}

.slide-up-leave-from {
  opacity: 1;
}

.slide-up-leave-from .action-layer {
  transform: translateY(0);
  opacity: 1;
}

.slide-up-leave-to {
  opacity: 0;
}

.slide-up-leave-to .action-layer {
  transform: translateY(-20px);
  opacity: 0;
}
</style>

