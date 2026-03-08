<template>
  <ActionLayer :visible="visible" @update:visible="$emit('update:visible', $event)">
    <div class="status-layer">
      <h3 class="text-xl font-bold mb-6">상태 설정</h3>
      <div class="space-y-3">
        <div
          v-for="status in statuses"
          :key="status.value"
          class="status-item p-4 border border-gray-200 rounded-lg cursor-pointer transition-colors"
          :class="currentStatus === status.value ? 'bg-blue-50 border-blue-500' : 'hover:bg-gray-50'"
          @click="handleSelectStatus(status.value)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div
                class="w-3 h-3 rounded-full"
                :class="status.color"
              ></div>
              <span class="font-medium text-gray-900">{{ status.label }}</span>
            </div>
            <el-icon v-if="currentStatus === status.value" class="text-blue-500">
              <Check />
            </el-icon>
          </div>
        </div>
      </div>
      
      <!-- 로그아웃 버튼 -->
      <div class="mt-6 pt-6 border-t border-gray-200">
        <div
          class="status-item p-4 border border-red-200 rounded-lg cursor-pointer transition-colors hover:bg-red-50"
          @click="handleLogout"
        >
          <div class="flex items-center gap-3">
            <el-icon class="text-red-500">
              <SwitchButton />
            </el-icon>
            <span class="font-medium text-red-600">로그아웃</span>
          </div>
        </div>
      </div>
    </div>
  </ActionLayer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Check, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import { updateUserStatus } from '@/services/statusService'
import ActionLayer from '@/components/layers/ActionLayer.vue'
import { STATUS_LIST } from '@/utils/userStatus'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'logout'])

const router = useRouter()
const userStore = useUserStore()
const currentStatus = ref(userStore.userStatus)

const statuses = STATUS_LIST

const handleSelectStatus = async (status) => {
  currentStatus.value = status
  const userId = userStore.user?.id
  if (userId) {
    await updateUserStatus(userId, status)
    userStore.setStatus(status)
  }
  emit('update:visible', false)
}

const handleLogout = () => {
  emit('logout')
}

onMounted(() => {
  currentStatus.value = userStore.userStatus
})
</script>

<style scoped>
.status-layer {
  padding: 20px 0;
}
</style>

