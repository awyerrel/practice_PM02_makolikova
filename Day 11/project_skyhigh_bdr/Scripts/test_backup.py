#!/usr/bin/env python3
"""
Тестовый скрипт бэкапа (не требует PostgreSQL)
"""

import os
import hashlib
import gzip
import json
from datetime import datetime
from pathlib import Path

# Создаем папки
LOCAL_WAL_DIR = Path('C:/postgresql/wal_archive')
LOG_DIR = Path('C:/backup_logs')
LOCAL_WAL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

print("=== Тестовый бэкап PostgreSQL WAL ===")
print(f"Время: {datetime.now()}")
print("=" * 40)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
wal_file = LOCAL_WAL_DIR / f"wal_{timestamp}.wal"

# Создаем тестовый файл
with open(wal_file, 'w') as f:
    f.write(f"=== PostgreSQL WAL Backup ===\n")
    f.write(f"Время: {timestamp}\n")
    f.write(f"Тип: Тестовый бэкап\n")
    f.write(f"Данные: Имитация WAL-логов PostgreSQL\n")
    f.write("=" * 40 + "\n")
    f.write("Транзакция 1: UPDATE flights SET status='ACTIVE' WHERE id=1\n")
    f.write("Транзакция 2: INSERT INTO bookings VALUES (12345, 'John Doe')\n")
    f.write("Транзакция 3: DELETE FROM cache WHERE expired=True\n")
    f.write("=" * 40 + "\n")
    f.write(f"Размер файла: {os.path.getsize(wal_file)} байт\n")

print(f"Создан WAL файл: {wal_file}")
print(f"Размер: {os.path.getsize(wal_file)} байт")

# Сжатие
compressed_file = LOCAL_WAL_DIR / f"wal_{timestamp}.wal.gz"
with open(wal_file, 'rb') as f_in:
    with gzip.open(compressed_file, 'wb') as f_out:
        f_out.write(f_in.read())

print(f"Сжат в: {compressed_file}")
print(f"Размер после сжатия: {os.path.getsize(compressed_file)} байт")

# Контрольная сумма
with open(compressed_file, 'rb') as f:
    checksum = hashlib.md5(f.read()).hexdigest()

print(f"Контрольная сумма (MD5): {checksum}")

# Сохраняем отчет
report = {
    "job_name": "postgres_wal_test",
    "status": "success",
    "timestamp": timestamp,
    "size_bytes": os.path.getsize(compressed_file),
    "checksum_md5": checksum,
    "type": "test_backup"
}

report_file = LOG_DIR / f"report_{timestamp}.json"
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"Отчет сохранен: {report_file}")

# Удаляем старые бэкапы (старше 7 дней)
cutoff = datetime.now().timestamp() - (7 * 24 * 3600)
count = 0
for f in LOCAL_WAL_DIR.glob("*.wal.gz"):
    if f.stat().st_mtime < cutoff:
        f.unlink()
        count += 1

print(f"Удалено старых файлов: {count}")

print("=" * 40)
print("Тестовый бэкап успешно завершен!")
print(f"Логи сохранены в: {LOG_DIR}")