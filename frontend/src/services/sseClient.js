/**
 * Bell 실시간 이벤트 클라이언트
 *
 * 이중 수신 방식:
 * 1. pywebview.evaluate_js()로 dispatch된 CustomEvent 'bell-sse' (가장 확실)
 * 2. HTTP EventSource (SSE) - fallback
 */

class SSEClient {
    constructor() {
        this.eventSource = null
        this.listeners = new Map()
        this.connected = false
        this._bellSseHandler = null
    }

    connect() {
        // ─── 방법 1: pywebview CustomEvent 수신 (항상 등록) ───────────────────
        if (!this._bellSseHandler) {
            this._bellSseHandler = (e) => {
                const { type, data } = e.detail || {}
                if (type) {
                    console.log(`[SSEClient] bell-sse event: ${type}`, data)
                    this._emit(type, data)
                    this.connected = true
                }
            }
            window.addEventListener('bell-sse', this._bellSseHandler)
            console.log('[SSEClient] bell-sse CustomEvent listener registered')
        }

        // ─── 방법 2: HTTP EventSource fallback ────────────────────────────────
        if (this.eventSource) return

        const url = `${window.location.origin}/events`
        console.log(`[SSEClient] Connecting EventSource to ${url}...`)

        try {
            this.eventSource = new EventSource(url)

            this.eventSource.onopen = () => {
                console.log('[SSEClient] EventSource connected')
                this.connected = true
                this._emit('status', { connected: true })
            }

            this.eventSource.onerror = () => {
                this.connected = false
                if (this.eventSource?.readyState === EventSource.CLOSED) {
                    this.eventSource = null
                    setTimeout(() => {
                        if (!this.eventSource) this._connectEventSource()
                    }, 5000)
                }
            }

            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    this._emit('message', data)
                } catch (e) { }
            }

            const customEvents = ['DB_UPDATE', 'NEW_CHAT', 'NEW_ANNOUNCEMENT', 'SYSTEM']
            customEvents.forEach(eventType => {
                this.eventSource.addEventListener(eventType, (event) => {
                    try {
                        const data = JSON.parse(event.data)
                        this._emit(eventType, data)
                    } catch (e) { }
                })
            })
        } catch (e) {
            console.warn('[SSEClient] EventSource not available:', e)
        }
    }

    _connectEventSource() {
        // 재연결 시도
        this.eventSource = null
        this.connect()
    }

    disconnect() {
        if (this._bellSseHandler) {
            window.removeEventListener('bell-sse', this._bellSseHandler)
            this._bellSseHandler = null
        }
        if (this.eventSource) {
            this.eventSource.close()
            this.eventSource = null
            this.connected = false
            console.log('[SSEClient] Disconnected')
        }
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, [])
        }
        this.listeners.get(eventType).push(callback)
        return () => this.off(eventType, callback)
    }

    off(eventType, callback) {
        const callbacks = this.listeners.get(eventType)
        if (callbacks) {
            const index = callbacks.indexOf(callback)
            if (index > -1) callbacks.splice(index, 1)
        }
    }

    _emit(eventType, data) {
        const callbacks = this.listeners.get(eventType)
        if (callbacks) {
            callbacks.forEach(cb => cb(data))
        }
    }
}

export const sseClient = new SSEClient()
