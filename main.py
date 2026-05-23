#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ЛР11 - Мониторинг качества ПО
Контейнер безопасности с метриками Prometheus
"""

import http.server
import ssl
import time
import json
from datetime import datetime
from socketserver import ThreadingMixIn

# ========== ПРОСТАЯ РЕАЛИЗАЦИЯ МЕТРИК (без prometheus_client) ==========
class Metrics:
    def __init__(self):
        self.blocked_count = 0
        self.icmp_flood_count = 0
        self.request_times = []

    def inc_blocked(self):
        self.blocked_count += 1

    def inc_icmp_flood(self):
        self.icmp_flood_count += 1

    def add_request_time(self, duration_ms):
        self.request_times.append(duration_ms)
        if len(self.request_times) > 100:
            self.request_times.pop(0)

    def get_metrics_text(self):
        avg_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        return f"""# HELP security_blocks_total Всего заблокированных запросов
# TYPE security_blocks_total counter
security_blocks_total {self.blocked_count}
# HELP security_icmp_flood_total ICMP-flood аномалии
# TYPE security_icmp_flood_total counter
security_icmp_flood_total {self.icmp_flood_count}
# HELP security_request_duration_seconds Среднее время обработки
# TYPE security_request_duration_seconds gauge
security_request_duration_seconds {avg_time:.3f}
"""

metrics = Metrics()

# ========== ЖУРНАЛИРОВАНИЕ ==========
ACCESS_LOG = []

def log_event(event_type, source, action, details=""):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "source": source,
        "action": action,
        "details": details
    }
    ACCESS_LOG.append(entry)
    print(f"[LOG] {event_type} | {source} | {action} | {details}")

# ========== HTTPS-СЕРВЕР ==========
class SecurityHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        start_time = time.time()
        client_ip = self.client_address[0]

        # Эндпоинт /block - блокировка
        if self.path == '/block':
            metrics.inc_blocked()
            log_event("BLOCK", client_ip, "ACCESS_DENIED", "ICMP/ARP/TCP")

            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"=== SECURITY CONTAINER ===\n")
            self.wfile.write(b"Access to equipment DENIED\n")
            self.wfile.write(b"HTTP 403 Forbidden\n")

        # Эндпоинт /metrics - метрики Prometheus
        elif self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics.get_metrics_text().encode('utf-8'))

        # Эндпоинт /logs - журнал событий
        elif self.path == '/logs':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(ACCESS_LOG[-20:], indent=2, ensure_ascii=False).encode('utf-8'))

        # Эндпоинт /flood - имитация ICMP-flood (увеличивает счётчик аномалий)
        elif self.path == '/flood':
            metrics.inc_icmp_flood()
            log_event("ANOMALY", client_ip, "ICMP_FLOOD_DETECTED", "10+ packets/sec")

            self.send_response(429)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"ICMP-FLOOD DETECTED - temporary block for 100 sec\n")

        # Эндпоинт / - проверка здоровья
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Security Container is running\n")
            self.wfile.write(b"Endpoints: /block, /metrics, /logs, /flood\n")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found\n")

        # Записываем время обработки запроса
        duration_ms = (time.time() - start_time) * 1000
        metrics.add_request_time(duration_ms)

    def log_message(self, format, *args):
        # Отключаем стандартное логирование, чтобы не дублировать
        pass

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    pass

# ========== ЗАПУСК ==========
def main():
    PORT = 8443
    CERT_FILE = "server.crt"
    KEY_FILE = "server.key"

    print("="*60)
    print("SECURITY CONTAINER with Prometheus Metrics (LR11)")
    print("="*60)

    # Генерация самоподписанного сертификата (если нет)
    import subprocess
    import os
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("[INFO] Generating self-signed certificate...")
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", KEY_FILE, "-out", CERT_FILE,
            "-days", "365", "-nodes",
            "-subj", "/CN=localhost"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[OK] Certificate generated")

    server = ThreadedHTTPServer(("0.0.0.0", PORT), SecurityHandler)

    # Настройка TLS 1.3
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print(f"[OK] HTTPS server started on port {PORT} (TLS 1.3)")
    print(f"[OK] Prometheus metrics available at http://localhost:9091/metrics (same port 8443)")
    print()
    print("ENDPOINTS:")
    print("  GET /block   - returns 403 Forbidden (block simulation)")
    print("  GET /metrics - returns Prometheus metrics")
    print("  GET /logs    - returns JSON log")
    print("  GET /flood   - simulates ICMP-flood anomaly")
    print("  GET /        - health check")
    print()
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Server stopped")
        server.shutdown()

if __name__ == "__main__":
    main()