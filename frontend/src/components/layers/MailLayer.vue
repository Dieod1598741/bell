<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="mail-layer">
      <h3 class="text-xl font-bold mb-6">이메일 확인 요청하기</h3>
      <div class="form-content">
        <el-input
          v-model="message"
          type="textarea"
          :rows="8"
          placeholder="이메일 확인 요청 메시지를 입력하세요"
          maxlength="500"
          show-word-limit
          class="mail-textarea"
        />
        <el-button 
          type="primary" 
          class="w-full submit-button" 
          @click="handleSubmit" 
          :disabled="!message.trim()"
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
    required: true
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const message = ref('')

const handleSubmit = () => {
  if (!message.value.trim()) return
  emit('submit', {
    userId: props.userId,
    message: message.value,
    type: 'mail'
  })
  message.value = ''
  emit('update:visible', false)
}
</script>

<style scoped>
.mail-layer {
  padding: 0;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.mail-textarea :deep(.el-textarea__inner) {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
}

.mail-textarea :deep(.el-textarea__inner:focus) {
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

