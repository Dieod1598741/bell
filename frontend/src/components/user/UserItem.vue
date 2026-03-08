<template>
  <div 
    class="user-item p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
    :class="{ 'bg-blue-50': selected }"
    :data-user-id="user.id"
    @click="$emit('click')"
  >
    <div class="flex items-center gap-3">
      <!-- 프로필 이미지 -->
      <UserAvatar :user="user" size="12" />
      
      <!-- 정보 -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <h3 class="font-semibold text-gray-900">{{ displayName }}</h3>
        </div>
        <p class="text-sm text-gray-600">
          {{ statusLabel }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusLabel } from '@/utils/userStatus'
import { getDisplayName } from '@/utils/userDisplay'
import UserAvatar from '@/components/common/UserAvatar.vue'

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const displayName = computed(() => getDisplayName(props.user))

const statusLabel = computed(() => {
  const status = props.user.user_status || 'offline'
  return getStatusLabel(status)
})
</script>

