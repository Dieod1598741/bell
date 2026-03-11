<template>
  <transition name="el-fade-in">
    <div v-if="hasUpdate" class="update-alert">
      <div class="update-content">
        <el-icon class="mr-2"><Bell /></el-icon>
        <span class="version-text">새 버전이 출시되었습니다: <strong>{{ latestVersion }}</strong></span>
        <div class="actions">
          <!-- 다운로드 중: 프로그레스바 -->
          <div v-if="isDownloading" class="progress-area">
            <el-progress
              :percentage="downloadProgress"
              :stroke-width="6"
              status="striped"
              striped-flow
              :duration="5"
              style="width: 160px;"
            />
            <span class="progress-text">{{ downloadProgress }}%</span>
          </div>
          <!-- 다운로드 전/완료 버튼 -->
          <template v-else>
            <el-button
              type="primary"
              size="small"
              class="update-btn"
              @click="handleUpdate"
            >
              {{ isDownloaded ? '설치 및 재시작' : '업데이트' }}
            </el-button>
          </template>
          <el-button
            type="info"
            size="small"
            link
            @click="hasUpdate = false"
          >
            나중에
          </el-button>
        </div>
        <!-- 에러 메시지 -->
        <span v-if="errorMsg" class="error-text">{{ errorMsg }}</span>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { backendService } from '@/services/backendService'
import { sseClient } from '@/services/sseClient'

const hasUpdate = ref(false)
const latestVersion = ref('')
const downloadUrl = ref('')
const releasePageUrl = ref('')    // 릴리즈 페이지 URL (항상 있음)
const assetAvailable = ref(false) // 빌드파일(.exe/.dmg) 첨부 여부
const isDownloading = ref(false)
const isDownloaded = ref(false)
const savedFilePath = ref('')
const downloadProgress = ref(0)
const errorMsg = ref('')          // 다운로드/설치 에러 메시지

const checkUpdate = async () => {
  try {
    console.log('[UpdateAlert] Checking for updates...')
    const result = await backendService.checkUpdate()
    console.log('[UpdateAlert] Check result:', result)
    if (result.success && result.hasUpdate) {
      hasUpdate.value = true
      latestVersion.value = result.latestVersion
      downloadUrl.value = result.downloadUrl || ''
      releasePageUrl.value = result.releasePageUrl || ''
      assetAvailable.value = result.assetAvailable ?? !!result.downloadUrl
    }
  } catch (error) {
    console.error('[UpdateAlert] 업데이트 확인 실패:', error)
  }
}

const handleUpdate = async () => {
  errorMsg.value = ''
  if (isDownloaded.value) {
    const r = await backendService.runInstaller(savedFilePath.value)
    if (!r?.success) {
      errorMsg.value = '설치 실패: ' + (r?.error || '다시 시도해주세요')
      setTimeout(() => backendService.openUrl(releasePageUrl.value || downloadUrl.value), 2000)
    }
    return
  }

  // 빌드파일 첨부 없는 릴리즈 → 브라우저로 릴리즈 페이지 열기
  if (!assetAvailable.value || !downloadUrl.value) {
    backendService.openUrl(releasePageUrl.value || downloadUrl.value)
    return
  }

  isDownloading.value = true
  downloadProgress.value = 0

  // SSE 진행률 이벤트 수신
  const unwatch = sseClient.on('DOWNLOAD_PROGRESS', (data) => {
    if (data.progress !== undefined) {
      downloadProgress.value = Math.min(data.progress, 100)
    }
  })

  try {
    const result = await backendService.downloadUpdate(downloadUrl.value)
    if (result.success && result.savePath) {
      downloadProgress.value = 100
      isDownloaded.value = true
      savedFilePath.value = result.savePath
    } else {
      errorMsg.value = result.error || '다운로드 실패 — 수동 설치 페이지로 이동합니다'
      setTimeout(() => backendService.openUrl(releasePageUrl.value || downloadUrl.value), 2000)
    }
  } catch (error) {
    console.error('[UpdateAlert] 다운로드 중 오류:', error)
    errorMsg.value = '다운로드 중 오류 — 수동 설치 페이지로 이동합니다'
    setTimeout(() => backendService.openUrl(releasePageUrl.value || downloadUrl.value), 2000)
  } finally {
    isDownloading.value = false
    unwatch()
  }
}

onMounted(async () => {
  if (window.pywebview?.api?.getPendingUpdate) {
    try {
      const pending = await backendService.getPendingUpdate()
      if (pending?.pendingPath) {
        isDownloaded.value = true
        savedFilePath.value = pending.pendingPath
        hasUpdate.value = true
        latestVersion.value = '(다운로드 완료)'
      }
    } catch (e) { /* 무시 */ }
  }
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
  background: #fdf6ec;
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
  color: #e6a23c;
}

.version-text strong {
  color: #cf9236;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 12px;
  color: #e6a23c;
  min-width: 32px;
}

.update-btn {
  background-color: #e6a23c;
  border-color: #e6a23c;
}

.update-btn:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}

.error-text {
  font-size: 11px;
  color: #f56c6c;
  margin-left: 4px;
}
</style>
