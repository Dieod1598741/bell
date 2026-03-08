<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="message-layer">
      <h3 class="text-xl font-bold mb-6">메시지 보내기</h3>
      <el-form @submit.prevent="handleSubmit">
        <el-form-item label="메시지">
          <el-input
            v-model="message"
            type="textarea"
            :rows="5"
            placeholder="메시지를 입력하세요"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="w-full" @click="handleSubmit" :disabled="!message.trim()">
            보내기
          </el-button>
        </el-form-item>
      </el-form>
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
    type: 'message'
  })
  message.value = ''
  emit('update:visible', false)
}
</script>

<style scoped>
.message-layer {
  padding: 20px 0;
}
</style>

