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
                # _initialized flag will be set in __init__
                # clients will be initialized in __init__
        return cls._instance

    def __init__(self):
        # Initialize clients and instance-level lock only on the first call to __init__
        if not hasattr(self, '_initialized'):
            self.clients = []
            self.lock = threading.Lock() # Instance-level lock for client list modification
            self._initialized = True
            print("[SSEManager] Initialized singleton")

    def add_client(self):
        q = queue.Queue()
        with self.lock: # Use the instance-level lock to protect clients list
            self.clients.append(q)
        print(f"[SSE] New client connected. Total clients: {len(self.clients)}")
        return q

    def remove_client(self, q):
            self.clients.remove(q)
            print(f"[SSE] Client disconnected. Total clients: {len(self.clients)}")

    def broadcast(self, event_type, data):
        """모든 클라이언트에게 이벤트 전송"""
        message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        for q in self.clients:
            q.put(message)

    def publish_update(self, table, action, record=None):
        """데이터 변경 이벤트 브로드캐스트"""
        self.broadcast("DB_UPDATE", {
            "table": table,
            "action": action,
            "record": record,
            "timestamp": time.time()
        })
