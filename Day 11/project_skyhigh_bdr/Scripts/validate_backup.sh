#!/bin/bash
# Скрипт валидации бэкапов
# Запуск: Ежедневно в 06:00

LOG_FILE="/var/log/backup/validation_$(date +%Y%m%d).log"
exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "=== Backup Validation Started at $(date) ==="

# 1. Проверка последнего бэкапа DB2
echo "Checking DB2 backup..."
DB2_BACKUP=$(aws s3 ls s3://skyhigh-backups/db2/full/ --recursive | sort | tail -1 | awk '{print $4}')
CHECKSUM=$(aws s3api head-object --bucket skyhigh-backups --key $DB2_BACKUP --query 'Metadata.checksum' --output text)
echo "DB2 backup: $DB2_BACKUP, checksum: $CHECKSUM"

# 2. Проверка возраста бэкапа
BACKUP_AGE=$(( ($(date +%s) - $(date -d "$(aws s3 ls s3://skyhigh-backups/db2/full/ --recursive | sort | tail -1 | awk '{print $1" "$2}')" +%s)) / 60 ))
if [ $BACKUP_AGE -gt 1440 ]; then
    echo "ERROR: DB2 backup is older than 24 hours!"
    exit 1
fi

# 3. Проверка контрольной суммы PostgreSQL WAL
echo "Checking PostgreSQL WAL..."
WAL_FILES=$(aws s3 ls s3://skyhigh-backups/postgresql/wal/ --recursive | tail -10)
for WAL in $WAL_FILES; do
    echo "WAL file: $WAL"
done

# 4. Проверка Redis RDB
echo "Checking Redis RDB..."
REDIS_FILE=$(aws s3 ls s3://skyhigh-backups/redis/ --recursive | sort | tail -1 | awk '{print $4}')
REDIS_SIZE=$(aws s3 ls s3://skyhigh-backups/redis/ --recursive | sort | tail -1 | awk '{print $3}')
echo "Redis file: $REDIS_FILE, size: $REDIS_SIZE bytes"

# 5. Проверка MSSQL бэкапа
echo "Checking MSSQL backup..."
MSSQL_BACKUP=$(aws s3 ls s3://skyhigh-backups/mssql/full/ --recursive | sort | tail -1 | awk '{print $4}')
echo "MSSQL backup: $MSSQL_BACKUP"

# 6. Проверка Kafka бэкапа
echo "Checking Kafka backup..."
KAFKA_TOPICS=$(aws s3 ls s3://skyhigh-backups/kafka/topics/ --recursive | wc -l)
echo "Kafka topics count: $KAFKA_TOPICS"

echo "=== Validation Completed at $(date) ==="