#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированное модульное тестирование контейнера безопасности
Вариант 31: защита пассивного физического оборудования от виртуальной сети
Фреймворк: pytest
"""

import pytest
import time
from datetime import datetime

# ============================================================
# Имитация контейнера безопасности
# ============================================================

class SecurityContainer:
    """Имитация контейнера безопасности для тестирования"""

    def __init__(self, equipment_ip="10.0.0.1"):
        self.equipment_ip = equipment_ip          # IP защищаемого оборудования
        self.packet_log = []                      # Журнал событий
        self.anomaly_flag = False                 # Флаг аномалии
        self.icmp_packet_count = 0                # Счётчик ICMP-пакетов для обнаружения флуда
        self.icmp_window_start = time.time()      # Время начала окна подсчёта
        self.arp_packet_count = 0
        self.tcp_scan_detected = False

    def process_icmp(self, source_ip, target_ip):
        """Обработка ICMP-пакета (ping)"""
        if target_ip == self.equipment_ip:
            # Блокировка пакета
            self.packet_log.append({
                "time": datetime.now(),
                "type": "ICMP",
                "source": source_ip,
                "target": target_ip,
                "action": "BLOCKED",
                "anomaly": False
            })
            # Проверка на флуд (аномалию)
            self._check_icmp_flood()
            return False  # пакет заблокирован
        return True  # пакет разрешён

    def _check_icmp_flood(self):
        """Обнаружение ICMP-флуда (аномалии)"""
        now = time.time()
        self.icmp_packet_count += 1

        # Если прошло больше 1 секунды — сбрасываем счётчик
        if now - self.icmp_window_start > 1.0:
            self.icmp_packet_count = 0
            self.icmp_window_start = now
        # Если за 1 секунду пришло 10+ пакетов — это аномалия
        elif self.icmp_packet_count >= 10:
            self.anomaly_flag = True
            # Отмечаем последний пакет как аномальный
            if self.packet_log:
                self.packet_log[-1]["anomaly"] = True
            # Добавляем отдельную запись об аномалии
            self.packet_log.append({
                "time": datetime.now(),
                "type": "ANOMALY",
                "source": None,
                "target": None,
                "action": "ICMP_FLOOD_DETECTED",
                "anomaly": True
            })

    def process_arp(self, source_mac, target_ip):
        """Обработка ARP-запроса"""
        if target_ip == self.equipment_ip:
            self.packet_log.append({
                "time": datetime.now(),
                "type": "ARP",
                "source": source_mac,
                "target": target_ip,
                "action": "BLOCKED",
                "anomaly": False
            })
            return False  # ARP-запрос заблокирован
        return True

    def process_tcp_syn(self, source_ip, target_ip, port):
        """Обработка TCP SYN-пакета (сканирование портов)"""
        if target_ip == self.equipment_ip:
            self.packet_log.append({
                "time": datetime.now(),
                "type": "TCP_SYN",
                "source": source_ip,
                "target": f"{target_ip}:{port}",
                "action": "BLOCKED",
                "anomaly": False
            })
            return False  # TCP-пакет заблокирован
        return True

    def get_log(self):
        """Получить весь журнал событий"""
        return self.packet_log

    def clear_log(self):
        """Очистить журнал"""
        self.packet_log = []
        self.anomaly_flag = False
        self.icmp_packet_count = 0

# ============================================================
# Автоматизированные тесты (pytest)
# ============================================================

@pytest.fixture
def container():
    """Фикстура: создаёт новый контейнер для каждого теста"""
    c = SecurityContainer()
    return c

def test_icmp_block(container):
    """ТК-01: Проверка блокировки ICMP (ping) к оборудованию"""
    # Отправляем ICMP-пакет на оборудование
    result = container.process_icmp("192.168.100.20", "10.0.0.1")
    # Ожидаем, что пакет заблокирован (return False)
    assert result == False
    # Проверяем, что событие записано в лог
    assert len(container.get_log()) >= 1
    # Проверяем, что действие — BLOCKED
    assert container.get_log()[-1]["action"] == "BLOCKED"
    print("[OK] test_icmp_block пройден")

def test_arp_block(container):
    """ТК-03: Проверка блокировки ARP-запросов к оборудованию"""
    result = container.process_arp("AA:BB:CC:DD:EE:FF", "10.0.0.1")
    assert result == False
    assert container.get_log()[-1]["type"] == "ARP"
    assert container.get_log()[-1]["action"] == "BLOCKED"
    print("[OK] test_arp_block пройден")

def test_tcp_scan_block(container):
    """ТК-04: Проверка блокировки TCP SYN-сканирования портов"""
    result = container.process_tcp_syn("192.168.100.20", "10.0.0.1", 22)
    assert result == False
    assert container.get_log()[-1]["type"] == "TCP_SYN"
    assert container.get_log()[-1]["action"] == "BLOCKED"
    print("[OK] test_tcp_scan_block пройден")

def test_icmp_flood_anomaly(container):
    """ТК-07: Проверка обнаружения ICMP-флуда как аномалии"""
    # Отправляем 12 ICMP-пакетов быстро (имитация флуда)
    for i in range(12):
        container.process_icmp("192.168.100.20", "10.0.0.1")
        time.sleep(0.05)  # небольшая задержка, но общее время < 1 секунды

    # Проверяем, что флаг аномалии установлен
    assert container.anomaly_flag == True

    # Проверяем, что в логе есть запись об аномалии
    anomalies = [e for e in container.get_log() if e.get("anomaly") == True]
    assert len(anomalies) >= 1
    print("[OK] test_icmp_flood_anomaly пройден")

# ============================================================
# Ручное приёмочное тестирование
# ============================================================

def manual_acceptance_test():
    """Функция для ручного тестирования с выводом лога"""
    print("\n" + "="*60)
    print("РУЧНОЕ ПРИЁМОЧНОЕ ТЕСТИРОВАНИЕ")
    print("Сценарий: атаки из виртуальной сети на пассивное оборудование")
    print("="*60)

    # Создаём контейнер
    cont = SecurityContainer(equipment_ip="10.0.0.1")

    print("\n[ШАГ 1] Имитация ICMP-запроса (ping) к оборудованию 10.0.0.1")
    cont.process_icmp("192.168.100.20", "10.0.0.1")

    print("[ШАГ 2] Имитация ARP-запроса к оборудованию 10.0.0.1")
    cont.process_arp("AA:BB:CC:DD:EE:FF", "10.0.0.1")

    print("[ШАГ 3] Имитация TCP SYN-сканирования порта 22 (SSH) оборудования")
    cont.process_tcp_syn("192.168.100.20", "10.0.0.1", 22)

    print("[ШАГ 4] Имитация ICMP-флуда (аномальная активность)")
    for i in range(15):
        cont.process_icmp("192.168.100.20", "10.0.0.1")
        time.sleep(0.05)

    print("\n" + "-"*60)
    print("ЖУРНАЛ БЕЗОПАСНОСТИ КОНТЕЙНЕРА")
    print("-"*60)
    print(f"{'Время':<12} | {'Тип':<10} | {'Источник':<18} | {'Действие':<20} | {'Аномалия'}")
    print("-"*80)

    for entry in cont.get_log():
        time_str = entry['time'].strftime('%H:%M:%S')
        type_str = entry['type']
        source_str = str(entry['source'])[:18] if entry['source'] else '-'
        action_str = entry['action']
        anomaly_str = "ДА" if entry['anomaly'] else "НЕТ"
        print(f"{time_str:<12} | {type_str:<10} | {source_str:<18} | {action_str:<20} | {anomaly_str}")

    print("-"*80)

    # Итог проверки
    print("\n=== РЕЗУЛЬТАТЫ ПРОВЕРКИ ===")

    # Проверяем, что все типы атак заблокированы
    icmp_blocks = [e for e in cont.get_log() if e['type'] == 'ICMP' and e['action'] == 'BLOCKED']
    arp_blocks = [e for e in cont.get_log() if e['type'] == 'ARP' and e['action'] == 'BLOCKED']
    tcp_blocks = [e for e in cont.get_log() if e['type'] == 'TCP_SYN' and e['action'] == 'BLOCKED']
    anomalies = [e for e in cont.get_log() if e.get('anomaly') == True]

    print(f"✓ ICMP-запросы заблокированы: {len(icmp_blocks)} записей")
    print(f"✓ ARP-запросы заблокированы: {len(arp_blocks)} записей")
    print(f"✓ TCP-сканирование заблокировано: {len(tcp_blocks)} записей")
    print(f"✓ Аномалии обнаружены: {len(anomalies)} записей")

    if len(icmp_blocks) > 0 and len(arp_blocks) > 0 and len(tcp_blocks) > 0 and len(anomalies) > 0:
        print("\n*** ВЕРДИКТ: ПРИЁМОЧНОЕ ТЕСТИРОВАНИЕ ПРОЙДЕНО ***")
        print("Контейнер корректно блокирует все попытки доступа к оборудованию")
        print("из виртуальной сети и регистрирует аномалии.")
    else:
        print("\n*** ВНИМАНИЕ: Тестирование НЕ пройдено — обнаружены отклонения ***")

    return cont.get_log()

# ============================================================
# Точка входа
# ============================================================

if __name__ == "__main__":
    print("Запуск автоматизированных тестов (pytest)...")
    print("="*50)

    # Запускаем pytest программно
    pytest.main([__file__, "-v", "--tb=short"])

    print("\n" + "="*50)
    print("Завершено. Запуск ручного приёмочного тестирования...")

    # Запускаем ручное тестирование
    manual_acceptance_test()