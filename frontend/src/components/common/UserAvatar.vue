<template>
  <div 
    class="user-avatar relative flex-shrink-0"
    :class="[
      { 'cursor-pointer': clickable },
      containerClass
    ]"
    :style="{ width: avatarSize, height: avatarSize }"
    @click="handleClick"
  >
    <!-- 프로필 이미지/이니셜 -->
    <div 
      class="rounded-full flex items-center justify-center text-white font-semibold overflow-hidden"
      :class="[
        !user?.avatar_color ? bgClass : '', // avatar_color가 없을 때만 bgClass 적용
        { 'shadow-md': shadow }
      ]"
      :style="{ 
        width: avatarSize, 
        height: avatarSize, 
        fontSize: textSize,
        backgroundColor: user?.avatar_color || undefined // avatar_color 우선 적용
      }"
    >
      <img 
        v-if="user?.avatar" 
        :src="user.avatar" 
        :alt="displayName"
        class="w-full h-full object-contain"
        :style="{ padding: '15%' }"
      />
      <span v-else>{{ displayInitial }}</span>
    </div>
    
    <!-- 상태 표시 (프로필 오른쪽 하단) -->
    <div
      v-if="showStatus"
      class="absolute rounded-full border-2 border-white"
      :class="[
        statusColor,
        { 'cursor-pointer hover:scale-110 transition-transform': statusClickable }
      ]"
      :style="statusStyle"
      :title="statusLabel"
      @click.stop="handleStatusClick"
    ></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusColor, getStatusLabel } from '@/utils/userStatus'
import { getDisplayName, getDisplayInitial } from '@/utils/userDisplay'

const props = defineProps({
  // 사용자 객체
  user: {
    type: Object,
    default: null
  },
  // 크기: 'xs' | 'sm' | 'md' | 'lg' | 'xl' 또는 숫자 (Tailwind 클래스)
  size: {
    type: [String, Number],
    default: 'md',
    validator: (value) => {
      if (typeof value === 'number') return true
      return ['xs', 'sm', 'md', 'lg', 'xl', '12', '16', '20', '24'].includes(value)
    }
  },
  // 상태 표시 여부
  showStatus: {
    type: Boolean,
    default: true
  },
  // 직접 상태 지정 (user.user_status 대신 사용)
  status: {
    type: String,
    default: null
  },
  // 클릭 가능 여부
  clickable: {
    type: Boolean,
    default: false
  },
  // 상태 클릭 가능 여부
  statusClickable: {
    type: Boolean,
    default: false
  },
  // 배경 색상 클래스
  bgClass: {
    type: String,
    default: 'bg-primary'
  },
  // 컨테이너 추가 클래스
  containerClass: {
    type: String,
    default: ''
  },
  // 그림자 표시
  shadow: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'status-click'])

const displayName = computed(() => getDisplayName(props.user))
const displayInitial = computed(() => getDisplayInitial(props.user))

// 크기 계산 (px 단위)
const avatarSize = computed(() => {
  const sizeMap = {
    xs: '24px',
    sm: '32px',
    md: '48px',
    lg: '64px',
    xl: '80px'
  }
  if (typeof props.size === 'number') {
    return `${props.size}px`
  }
  return sizeMap[props.size] || sizeMap.md
})

// 텍스트 크기 계산
const textSize = computed(() => {
  const sizeMap = {
    xs: '10px',
    sm: '12px',
    md: '16px',
    lg: '20px',
    xl: '24px'
  }
  if (typeof props.size === 'number') {
    return `${Math.floor(props.size * 0.4)}px`
  }
  return sizeMap[props.size] || sizeMap.md
})

// 상태 인디케이터 스타일
const statusStyle = computed(() => {
  const sizeMap = {
    xs: { width: '8px', height: '8px', bottom: '0px', right: '0px' },
    sm: { width: '10px', height: '10px', bottom: '0px', right: '0px' },
    md: { width: '16px', height: '16px', bottom: '-1px', right: '-1px' },
    lg: { width: '20px', height: '20px', bottom: '-1px', right: '-1px' },
    xl: { width: '24px', height: '24px', bottom: '0px', right: '0px' }
  }
  
  if (typeof props.size === 'number') {
    const statusSize = Math.floor(props.size * 0.25)
    return {
      width: `${statusSize}px`,
      height: `${statusSize}px`,
      bottom: `${Math.floor(props.size * -0.05)}px`,
      right: `${Math.floor(props.size * -0.05)}px`
    }
  }
  
  const style = sizeMap[props.size] || sizeMap.md
  return {
    width: style.width,
    height: style.height,
    bottom: style.bottom,
    right: style.right
  }
})

const statusColor = computed(() => {
  const userStatus = props.status || props.user?.user_status || 'offline'
  return getStatusColor(userStatus)
})

const statusLabel = computed(() => {
  const userStatus = props.status || props.user?.user_status || 'offline'
  return getStatusLabel(userStatus)
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}

const handleStatusClick = () => {
  if (props.statusClickable) {
    emit('status-click')
  }
}
</script>

<style scoped>
/* Tailwind 동적 클래스가 제대로 적용되도록 */
</style>

