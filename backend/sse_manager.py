import json
import queue
import threading
import time

class SSEManager:
    """SSE 클라이언트 관리 및 이벤트 브로드캐스트"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SSEManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.clients = []
            self.lock = threading.Lock()
            self._initialized = True
            print("[SSEManager] Initialized singleton")


        q = queue.Queue()
        with self.lock:
            self.clients.append(q)
        print(f"[SSE] New client connected. Total clients: {len(self.clients)}")
        return q

    def remove_client(self, q):
        with self.lock:
            try:
                self.clients.remove(q)
            except ValueError:
                pass
        print(f"[SSE] Client disconnected. Total clients: {len(self.clients)}")

    def broadcast(self, event_type, data):
        """모든 클라이언트에게 이벤트 전송 (SSE큐 + pywebview evaluate_js 이중 전송)"""
        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        # 1. SSE 큐 전송 (HTTP EventSource 연결된 경우)
        with self.lock:
            dead = []
            for q in self.clients:
                try:
                    q.put(message)
                except Exception:
                    dead.append(q)
            for q in dead:
                try:
                    self.clients.remove(q)
                except ValueError:
                    pass

        # 2. pywebview evaluate_js 직접 전송 (가장 확실한 방법)
        try:
            import webview
            payload_json = json.dumps({"type": event_type, "data": data})
            js = f"""
(function() {{
    try {{
        var ev = new CustomEvent('bell-sse', {{detail: {payload_json}}});
        window.dispatchEvent(ev);
    }} catch(e) {{}}
}})();
"""
            for win in webview.windows:
                try:
                    win.evaluate_js(js)
                except Exception:
                    pass
        except Exception as e:
            pass  # webview 미사용 환경에서는 무시

    def publish_update(self, table, action, record=None):
        """데이터 변경 이벤트 브로드캐스트"""
        self.broadcast("DB_UPDATE", {
            "table": table,
            "action": action,
            "record": record,
            "timestamp": time.time()
        })
