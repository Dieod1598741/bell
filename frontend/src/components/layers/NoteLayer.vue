<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="note-layer">
      <h3 class="text-xl font-bold mb-6">쪽지 보내기</h3>
      <div class="form-content">
        <el-input
          v-model="note"
          type="textarea"
          :rows="8"
          placeholder="쪽지 내용을 입력하세요"
          maxlength="500"
          show-word-limit
          class="note-textarea"
        />
        <el-button 
          type="primary" 
          class="w-full submit-button" 
          @click="handleSubmit" 
          :disabled="!note.trim()"
        >
          보내기
        </el-button>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { ref } from 'vue'
import ActionLayer from '@/components/layers/ActionLayer.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  userId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const note = ref('')

const handleSubmit = () => {
  if (!note.value.trim() || !props.userId) return
  emit('submit', {
    userId: props.userId,
    message: note.value,
    type: 'note'
  })
  note.value = ''
  emit('update:visible', false)
}
</script>

<style scoped>
.note-layer {
  padding: 0;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.note-textarea :deep(.el-textarea__inner) {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
}

.note-textarea :deep(.el-textarea__inner:focus) {
  border-color: #409EFF;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.submit-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}
</style>

