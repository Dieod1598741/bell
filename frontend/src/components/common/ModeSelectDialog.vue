<template>
  <el-dialog
    v-model="dialogVisible"
    title="모드 선택"
    width="90%"
    :before-close="handleClose"
  >
    <div class="space-y-3">
      <el-button 
        type="primary" 
        size="large"
        class="w-full"
        @click="handleChat"
      >
        <el-icon class="mr-2"><ChatDotRound /></el-icon>
        채팅하기
      </el-button>
      <el-button 
        type="success" 
        size="large"
        class="w-full"
        @click="handleNotification"
      >
        <el-icon class="mr-2"><Bell /></el-icon>
        알림 전송
      </el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { ChatDotRound, Bell } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'chat', 'notification'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleClose = () => {
  dialogVisible.value = false
}

const handleChat = () => {
  emit('chat', props.user)
  handleClose()
}

const handleNotification = () => {
  emit('notification', props.user)
  handleClose()
}
</script>






