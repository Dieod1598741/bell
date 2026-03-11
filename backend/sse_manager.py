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
            self._webview_window = None  # pywebview window 직접 참조
            self._initialized = True
            print("[SSEManager] Initialized singleton")

    def register_window(self, window):
        """pywebview window 직접 참조 등록 (window 생성 후 즉시 호출)"""
        self._webview_window = window
        print(f"[SSEManager] pywebview window registered: {window}")

    def add_client(self):
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

    def subscribe(self):
        """add_client의 alias - bell_sse_test.py 등에서 사용"""
        return self.add_client()

    def unsubscribe(self, q):
        """remove_client의 alias - bell_sse_test.py 등에서 사용"""
        self.remove_client(q)

    def broadcast(self, event_type, data):
        """모든 클라이언트에게 이벤트 전송 (SSE큐 + pywebview window 직접 dispatch 이중 전송)"""
        # HTTP SSE 응답용 포맷 문자열 (SimpleWebHandler가 .encode()로 직접 전송)
        message_str = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

        # 1. HTTP SSE 큐 전송 (문자열로 저장 — encode() 호환)
        with self.lock:
            dead = []
            for q in self.clients:
                try:
                    q.put(message_str)  # ← 반드시 str 형태로 (SimpleWebHandler에서 .encode())
                except Exception:
                    dead.append(q)
            for q in dead:
                try:
                    self.clients.remove(q)
                except ValueError:
                    pass

        # 2. pywebview window 직접 evaluate_js (가장 확실한 방법, 윈도우/맥 모두 지원)
        win = self._webview_window
        if win is not None:
            def _push():
                try:
                    payload_json = json.dumps({"type": event_type, "data": data})
                    js = f"""
(function() {{
    try {{
        var ev = new CustomEvent('bell-sse', {{detail: {payload_json}}});
        window.dispatchEvent(ev);
    }} catch(e) {{}}
}})();
"""
                    win.evaluate_js(js)
                except Exception as e:
                    print(f"[SSEManager] evaluate_js 실패: {e}")

            threading.Thread(target=_push, daemon=True).start()

    def publish_update(self, table, action, record=None):
        """데이터 변경 이벤트 브로드캐스트"""
        self.broadcast("DB_UPDATE", {
            "table": table,
            "action": action,
            "record": record,
            "timestamp": time.time()
        })
