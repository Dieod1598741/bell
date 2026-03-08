<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="meeting-layer">
      <h3 class="text-xl font-bold mb-6">회의 요청하기</h3>
      <div class="form-content">
        <div class="form-group-with-label">
          <span class="input-label-top">회의 시간</span>
          <el-date-picker
            v-model="meetingTime"
            type="datetime"
            placeholder="회의 시간을 선택하세요"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm"
            class="w-full"
          />
        </div>
        <div class="form-group-with-label">
          <span class="input-label-top">회의 장소</span>
          <el-input
            v-model="meetingPlace"
            placeholder="회의 장소를 입력하세요"
          />
        </div>
        <div class="form-group-with-label">
          <span class="input-label-top">메모</span>
          <el-input
            v-model="memo"
            type="textarea"
            :rows="4"
            placeholder="간단한 메모를 입력하세요"
            maxlength="200"
            show-word-limit
            class="memo-textarea"
          />
        </div>
        <el-button 
          type="primary" 
          class="w-full submit-button" 
          @click="handleSubmit" 
          :disabled="!meetingTime || !meetingPlace"
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

const meetingTime = ref('')
const meetingPlace = ref('')
const memo = ref('')

const handleSubmit = () => {
  if (!meetingTime.value || !meetingPlace.value) return
  emit('submit', {
    userId: props.userId,
    message: `회의 요청\n시간: ${meetingTime.value}\n장소: ${meetingPlace.value}${memo.value ? `\n메모: ${memo.value}` : ''}`,
    type: 'meeting',
    meetingTime: meetingTime.value,
    meetingPlace: meetingPlace.value,
    memo: memo.value
  })
  meetingTime.value = ''
  meetingPlace.value = ''
  memo.value = ''
  emit('update:visible', false)
}
</script>

<style scoped>
.meeting-layer {
  padding: 0;
}

.form-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group-with-label {
  position: relative;
}

.input-label-top {
  position: absolute;
  top: -8px;
  left: 12px;
  font-size: 11px;
  font-weight: 500;
  color: #6b7280;
  padding: 0 4px;
  z-index: 1;
  background: white;
}

.memo-textarea :deep(.el-textarea__inner) {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
}

.memo-textarea :deep(.el-textarea__inner:focus) {
  border-color: #409EFF;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.submit-button {
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  min-height: 40px;
}

:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  border-radius: 12px;
  padding: 8px 16px;
  min-height: 40px;
}
</style>

