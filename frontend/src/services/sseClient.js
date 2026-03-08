/**
 * PostgreSQL/Python 백엔드의 SSE(Server-Sent Events) 이벤트를 수신하는 클라이언트
 */

class SSEClient {
    constructor() {
        this.eventSource = null;
        this.listeners = new Map();
        this.connected = false;
    }

    connect() {
        if (this.eventSource) return;

        // 현재 페이지의 origin과 포트를 사용 (SimpleWebServer가 같은 곳에서 서빙하므로)
        const url = `${window.location.origin}/events`;
        console.log(`[SSEClient] Connecting to ${url}...`);

        this.eventSource = new EventSource(url);

        this.eventSource.onopen = () => {
            console.log('[SSEClient] Connection established');
            this.connected = true;
            this._emit('status', { connected: true });
        };

        this.eventSource.onerror = (error) => {
            console.error('[SSEClient] Connection error:', error);
            this.connected = false;
            this._emit('error', error);

            // 재연결 로직 (필요시)
            if (this.eventSource.readyState === EventSource.CLOSED) {
                this.eventSource = null;
                setTimeout(() => this.connect(), 3000);
            }
        };

        // 일반 메시지 처리
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._emit('message', data);
            } catch (e) {
                console.warn('[SSEClient] Failed to parse message data:', event.data);
            }
        };

        // 커스텀 이벤트 처리
        const customEvents = ['DB_UPDATE', 'NEW_CHAT', 'NEW_ANNOUNCEMENT'];
        customEvents.forEach(eventType => {
            this.eventSource.addEventListener(eventType, (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._emit(eventType, data);
                } catch (e) {
                    console.warn(`[SSEClient] Failed to parse ${eventType} data:`, event.data);
                }
            });
        });
    }

    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.connected = false;
            console.log('[SSEClient] Connection closed');
        }
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(callback);
        return () => this.off(eventType, callback);
    }

    off(eventType, callback) {
        const callbacks = this.listeners.get(eventType);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    _emit(eventType, data) {
        const callbacks = this.listeners.get(eventType);
        if (callbacks) {
            callbacks.forEach(cb => cb(data));
        }
    }
}

export const sseClient = new SSEClient();
