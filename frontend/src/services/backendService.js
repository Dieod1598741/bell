/**
 * Python 백엔드 API와 통신하기 위한 전송 레이어
 */

const callBackend = async (methodName, ...args) => {
    // 최대 5회 재시도 (초기 로딩 시 브리지가 늦게 준비될 수 있음)
    let retries = 5;
    while (retries > 0) {
        if (window.pywebview && window.pywebview.api) {
            try {
                const result = await window.pywebview.api[methodName](...args);
                return result;
            } catch (error) {
                console.error(`[BackendService] Error calling ${methodName}:`, error);
                return { success: false, error: error.toString() };
            }
        }
        console.warn(`[BackendService] pywebview.api not ready for ${methodName}. Retrying... (${retries})`);
        await new Promise(resolve => setTimeout(resolve, 500));
        retries--;
    }

    console.error(`[BackendService] pywebview.api NOT READY after retries for ${methodName}`);
    return { success: false, error: 'API not ready' };
};

export const backendService = {
    // User
    getUserInfo: () => callBackend('getUserInfo'),
    saveUserInfo: (data) => callBackend('saveUserInfo', data),
    getUserById: (userId) => callBackend('getUserById', userId),
    getUserStatus: () => callBackend('getUserStatus'),
    saveUserStatus: (status) => callBackend('saveUserStatus', status),
    getAllUsers: () => callBackend('getAllUsers'),

    // Chat
    getMessages: (userId, currentUserId) => callBackend('getMessages', userId, currentUserId),
    sendChatMessage: (senderId, targetId, content) => callBackend('sendChatMessage', senderId, targetId, content),
    markMessageRead: (messageId, type) => callBackend('markMessageRead', messageId, type),

    // Inbox / Announcements
    getInbox: (userId) => callBackend('getInbox', userId),
    sendAnnouncement: (userIds, message) => callBackend('sendAnnouncement', userIds, message),

    // Hardware / Settings
    getHardwareId: () => callBackend('getHardwareId'),
    getLoginSettings: () => callBackend('getLoginSettings'),
    saveLoginSettings: (settings) => callBackend('saveLoginSettings', settings),

    // Notification
    showNotification: (title, message, type) => callBackend('showNotification', title, message, type),

    // System / Update
    checkUpdate: () => callBackend('checkUpdate'),
    downloadUpdate: (url) => callBackend('downloadUpdate', url),
    runInstaller: (filePath) => callBackend('runInstaller', filePath),
    getPendingUpdate: () => callBackend('getPendingUpdate'),
    openUrl: (url) => callBackend('openUrl', url)
};
