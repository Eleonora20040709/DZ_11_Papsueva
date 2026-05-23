#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.error
import ssl
import time
import json
import os

# Отключаем проверку SSL (для самоподписанного сертификата)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Конфигурация
METRICS_URL = "https://localhost:8444/metrics"
SCRAPE_INTERVAL = 5  # секунд

# Пороги для алёртов
ALERT_THRESHOLDS = {
    "high_block_rate": 10,      # блокировок в секунду (среднее)
    "icmp_flood": 1,            # появление ICMP-flood
    "high_response_time": 100   # мс
}

# Храним историю для расчёта rate
previous_metrics = {}

def fetch_metrics():
    """Забирает метрики с /metrics"""
    try:
        req = urllib.request.Request(METRICS_URL, method='GET')
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            data = response.read().decode('utf-8')
            return parse_metrics(data)
    except Exception as e:
        print(f"[ERROR] Failed to fetch metrics: {e}")
        return {}

def parse_metrics(data):
    """Парсит текстовый формат Prometheus"""
    metrics = {}
    for line in data.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '{' in line:
            # Метрика с метками: security_blocks_total{attack_type="generic"} 135
            name_part, value = line.rsplit(' ', 1)
            name = name_part.split('{')[0]
            labels = {}
            # Простой парсинг меток
            label_part = name_part.split('{')[1].rstrip('}')
            for pair in label_part.split(','):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    labels[k] = v.strip('"')
            key = f"{name}_{json.dumps(labels, sort_keys=True)}"
            metrics[key] = float(value)
        else:
            # Метрика без меток
            parts = line.rsplit(' ', 1)
            if len(parts) == 2:
                metrics[parts[0]] = float(parts[1])
    return metrics

def check_alerts(metrics, previous):
    """Проверяет алёрты на основе метрик"""
    alerts = []

    # Алёрт 1: Высокая частота блокировок
    current_total = metrics.get('security_blocks_total_{"attack_type":"generic"}', 0)
    prev_total = previous.get('security_blocks_total_{"attack_type":"generic"}', 0)
    rate = (current_total - prev_total) / SCRAPE_INTERVAL if SCRAPE_INTERVAL > 0 else 0

    if rate > ALERT_THRESHOLDS["high_block_rate"]:
        alerts.append({
            "name": "HighBlockRate",
            "severity": "warning",
            "summary": f"Высокая частота блокировок: {rate:.1f}/сек",
            "description": f"Более {ALERT_THRESHOLDS['high_block_rate']} блокировок в секунду"
        })

    # Алёрт 2: ICMP-flood аномалия
    icmp_flood = metrics.get('security_icmp_flood_total', 0)
    prev_icmp_flood = previous.get('security_icmp_flood_total', 0)
    if icmp_flood > prev_icmp_flood:
        alerts.append({
            "name": "ICMPFloodDetected",
            "severity": "critical",
            "summary": "Обнаружена ICMP-flood аномалия",
            "description": "Зафиксирован ICMP-flood на контейнере безопасности"
        })

    # Алёрт 3: Высокое время отклика
    avg_time = metrics.get('security_request_duration_seconds', 0) * 1000  # в мс
    if avg_time > ALERT_THRESHOLDS["high_response_time"]:
        alerts.append({
            "name": "HighResponseTime",
            "severity": "warning",
            "summary": f"Высокое время отклика: {avg_time:.0f} мс",
            "description": f"Время отклика превышает {ALERT_THRESHOLDS['high_response_time']} мс"
        })

    return alerts, rate

def clear_screen():
    """Очищает экран (для анимации дашборда)"""
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_dashboard(metrics, alerts, rate):
    """Рисует текстовый дашборд в терминале"""
    clear_screen()

    # Получаем значения
    blocks_generic = int(metrics.get('security_blocks_total_{"attack_type":"generic"}', 0))
    blocks_arp = int(metrics.get('security_blocks_total_{"attack_type":"arp"}', 0))
    blocks_tcp = int(metrics.get('security_blocks_total_{"attack_type":"tcp_syn"}', 0))
    icmp_flood = int(metrics.get('security_icmp_flood_total', 0))
    avg_time_ms = metrics.get('security_request_duration_seconds', 0) * 1000

    # Максимум для масштабирования баров
    max_blocks = max(blocks_generic, blocks_arp, blocks_tcp, 1)

    def bar(value, max_val, width=20):
        if max_val == 0:
            return " " * width
        filled = int(value / max_val * width)
        return "█" * filled + "░" * (width - filled)

    print("=" * 70)
    print("📊 GRAFANA DASHBOARD (текстовый режим) - Security Container Quality")
    print("=" * 70)
    print(f"⏱️  Last scrape: {time.strftime('%Y-%m-%d %H:%M:%S')}  |  Interval: {SCRAPE_INTERVAL}s")
    print("-" * 70)
    print()
    print("📈 TOTAL BLOCKS BY ATTACK TYPE:")
    print(f"   generic    │ {bar(blocks_generic, max_blocks)} {blocks_generic}")
    print(f"   ARP        │ {bar(blocks_arp, max_blocks)} {blocks_arp}")
    print(f"   TCP SYN    │ {bar(blocks_tcp, max_blocks)} {blocks_tcp}")
    print()
    print("⚡ BLOCK RATE (avg per second):")
    bar_rate = min(int(rate * 2), 30)  # масштабирование: 10/сек = 20 символов
    print(f"   █{'█' * bar_rate}{'░' * (30 - bar_rate)} {rate:.2f}/сек")
    print(f"   Порог алёрта: > {ALERT_THRESHOLDS['high_block_rate']}/сек")
    print()
    print("🚨 ICMP-FLOOD ANOMALIES:")
    print(f"   security_icmp_flood_total = {icmp_flood}")
    if icmp_flood > 0:
        print("   ⚠️  Аномалии зафиксированы!")
    print()
    print("⏱️  REQUEST DURATION (среднее):")
    bar_time = min(int(avg_time_ms / 5), 30)
    print(f"   █{'█' * bar_time}{'░' * (30 - bar_time)} {avg_time_ms:.1f} мс")
    print(f"   Порог алёрта: > {ALERT_THRESHOLDS['high_response_time']} мс")
    print()
    print("-" * 70)
    print("🔔 ACTIVE ALERTS:")
    if alerts:
        for alert in alerts:
            severity_icon = "🔴 CRITICAL" if alert['severity'] == 'critical' else "🟡 WARNING"
            print(f"   [{severity_icon}] {alert['name']}")
            print(f"       {alert['summary']}")
    else:
        print("   ✅ Нет активных алёртов")
    print("-" * 70)
    print("💡 Endpoints to simulate attacks:")
    print("   В другом терминале запустите:")
    print("   curl -k https://localhost:8444/block/icmp")
    print("   curl -k https://localhost:8444/block/arp")
    print("   curl -k https://localhost:8444/block/tcp")
    print("   curl -k https://localhost:8444/flood")
    print("=" * 70)

def main():
    global previous_metrics

    print("🔄 Запуск мониторинга (имитация Prometheus + Grafana)...")
    print(f"📡 Сбор метрик с {METRICS_URL}")
    print(f"⏱️  Интервал: {SCRAPE_INTERVAL} секунд")
    print("=" * 70)
    print()
    print("⚠️  Убедитесь, что контейнер безопасности запущен (python main.py)")
    print("   в другом терминале!")
    print()
    print("Нажмите Ctrl+C для выхода")
    print()

    time.sleep(3)

    try:
        while True:
            metrics = fetch_metrics()
            if metrics:
                alerts, rate = check_alerts(metrics, previous_metrics)
                draw_dashboard(metrics, alerts, rate)
                previous_metrics = metrics.copy()
            else:
                print("[WARN] Не удалось получить метрики. Проверьте, запущен ли контейнер.")

            time.sleep(SCRAPE_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    main()