<template>
  <transition name="el-fade-in">
    <div v-if="hasUpdate" class="update-alert">
      <div class="update-content">
        <el-icon class="mr-2"><Bell /></el-icon>
        <span class="version-text">새 버전이 출시되었습니다: <strong>{{ latestVersion }}</strong></span>
        <div class="actions">
          <el-button 
            type="primary" 
            size="small" 
            class="update-btn"
            @click="handleUpdate"
          >
            업데이트
          </el-button>
          <el-button 
            type="info" 
            size="small" 
            link
            @click="hasUpdate = false"
          >
            나중에
          </el-button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { backendService } from '@/services/backendService'

const hasUpdate = ref(false)
const latestVersion = ref('')
const downloadUrl = ref('')

const checkUpdate = async () => {
  try {
    const result = await backendService.checkUpdate()
    if (result.success && result.hasUpdate) {
      hasUpdate.value = true
      latestVersion.value = result.latestVersion
      downloadUrl.value = result.downloadUrl
    }
  } catch (error) {
    console.error('[UpdateAlert] 업데이트 확인 실패:', error)
  }
}

const handleUpdate = () => {
  if (downloadUrl.value) {
    backendService.openUrl(downloadUrl.value)
  }
}

onMounted(() => {
  // 시작 후 3초 뒤에 업데이트 확인 (초기 로딩 부하 방지)
  setTimeout(checkUpdate, 3000)
})
</script>

<style scoped>
.update-alert {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #fdf6ec; /* Warning light background */
  border-bottom: 1px solid #faecd8;
  padding: 8px 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.update-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #e6a23c; /* Warning color */
}

.version-text strong {
  color: #cf9236;
}

.actions {
  display: flex;
  gap: 8px;
}

.update-btn {
  background-color: #e6a23c;
  border-color: #e6a23c;
}

.update-btn:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}
</style>
