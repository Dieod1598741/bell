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
            :loading="isDownloading"
            @click="handleUpdate"
          >
            {{ isDownloaded ? '설치 및 재시작' : (isDownloading ? '다운로드 중...' : '업데이트') }}
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
const isDownloading = ref(false)
const isDownloaded = ref(false)
const savedFilePath = ref('')

const checkUpdate = async () => {
  try {
    console.log('[UpdateAlert] Checking for updates...');
    const result = await backendService.checkUpdate()
    console.log('[UpdateAlert] Check result:', result);
    if (result.success && result.hasUpdate) {
      hasUpdate.value = true
      latestVersion.value = result.latestVersion
      downloadUrl.value = result.downloadUrl
      console.log('[UpdateAlert] Update found:', latestVersion.value);
    } else {
      console.log('[UpdateAlert] No update found or check failed');
    }
  } catch (error) {
    console.error('[UpdateAlert] 업데이트 확인 실패:', error)
  }
}

const handleUpdate = async () => {
  if (isDownloaded.value) {
    // 이미 다운로드됨 -> 설치 프로그램 실행
    await backendService.runInstaller(savedFilePath.value)
    return
  }

  if (!downloadUrl.value) return
  
  try {
    isDownloading.value = true
    // 백엔드에 다운로드 요청
    const result = await backendService.downloadUpdate(downloadUrl.value)
    if (result.success) {
      isDownloaded.value = true
      savedFilePath.value = result.savePath
    } else {
      // 실패 시 브라우저라도 열어줌
      backendService.openUrl(downloadUrl.value)
    }
  } catch (error) {
    console.error('[UpdateAlert] 다운로드 중 오류:', error)
    backendService.openUrl(downloadUrl.value)
  } finally {
    isDownloading.value = false
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
