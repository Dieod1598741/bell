/**
 * Python 백엔드 API와 통신하기 위한 전송 레이어
 */

const callBackend = async (methodName, ...args) => {
    if (!window.pywebview || !window.pywebview.api) {
        console.error(`[BackendService] pywebview.api not ready for ${methodName}`);
        return { success: false, error: 'API not ready' };
    }

    try {
        const result = await window.pywebview.api[methodName](...args);
        return result;
    } catch (error) {
        console.error(`[BackendService] Error calling ${methodName}:`, error);
        return { success: false, error: error.toString() };
    }
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
    openUrl: (url) => callBackend('openUrl', url)
};
