markdown
# Инструкция по аварийному восстановлению (Recovery Runbook)
**Компания:** SkyHigh Airlines
**Версия:** 1.0
**Дата:** 17.06.2026
**Сценарий:** Полный отказ Primary Data Center (us-east-1)
**Цель:** Восстановить все сервисы в резервном ЦОД (eu-central-1) за ≤ 4 часа


## ШАГ 1: Подтверждение инцидента (1 минута)

```bash
curl -I https://api.skyhigh.aero/health
curl -I https://disp.skyhigh.aero/health
aws health describe-events --region us-east-1
ШАГ 2: Активация команды (2 минуты)
bash
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"CRITICAL: Primary DC down. Starting DR procedure!"}' \
<SLACK_WEBHOOK_URL>
ШАГ 3: Переключение DNS (2 минуты)
bash
aws route53 change-resource-record-sets --hosted-zone-id ZXXXXXXXXXX \
--change-batch file://failover-dns.json

dig api.skyhigh.aero
ВОССТАНОВЛЕНИЕ DB2 (БРОНИРОВАНИЕ) - 15 МИНУТ
ШАГ 4: Запуск инфраструктуры DB2 (3 минуты)
bash
aws ec2 run-instances \
    --image-id ami-db2-prod-eu-central-1 \
    --instance-type r5.4xlarge \
    --region eu-central-1 \
    --security-group-ids sg-db2-dr \
    --subnet-id subnet-dr-db2

DB2_IP=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=db2-dr-primary" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ssh -i skyhigh-key.pem ec2-user@$DB2_IP
ШАГ 5: Восстановление из полного бэкапа (5 минут)
bash
aws s3 cp s3://skyhigh-backups/db2/full/backup_latest.db2 /tmp/

EXPECTED_CHECKSUM=$(aws s3api head-object --bucket skyhigh-backups --key db2/full/backup_latest.db2 --query 'Metadata.checksum' --output text)
ACTUAL_CHECKSUM=$(sha256sum /tmp/backup_latest.db2 | awk '{print $1}')

if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
    echo "ERROR: Checksum mismatch!"
    exit 1
fi

db2 RESTORE DATABASE SKYHIGH FROM '/tmp/backup_latest.db2'
ШАГ 6: Применение транзакционных логов (5 минут)
bash
aws s3 cp s3://skyhigh-backups/db2/archivelogs/ /db2/archivelogs/ --recursive

db2 ROLLFORWARD DATABASE SKYHIGH TO 2026-06-17-14.24.59.000000 \
USING LOCAL TIME AND STOP
ШАГ 7: Проверка консистентности DB2 (2 минуты)
sql
db2 "SELECT COUNT(*) FROM BOOKING.ACTIVE_BOOKINGS WHERE BOOKING_DATE = CURRENT DATE"
db2 "SELECT SUM(AMOUNT) FROM BOOKING.TRANSACTIONS WHERE TRANSACTION_DATE = CURRENT DATE"
ВОССТАНОВЛЕНИЕ POSTGRESQL (ДИСПЕТЧЕРСКАЯ) - 30 МИНУТ
ШАГ 8: Запуск PostgreSQL (5 минут)
bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier skyhigh-disp-dr \
    --db-snapshot-identifier skyhigh-disp-snapshot-latest \
    --region eu-central-1

aws rds wait db-instance-available --db-instance-identifier skyhigh-disp-dr

PG_HOST=$(aws rds describe-db-instances --db-instance-identifier skyhigh-disp-dr --query 'DBInstances[0].Endpoint.Address' --output text)
ШАГ 9: Восстановление из WAL (20 минут)
bash
cat > /tmp/recovery.conf << 'EOF'
restore_command = 'aws s3 cp s3://skyhigh-backups/postgres/wal/%f %p'
recovery_target_time = '2026-06-17 14:24:59'
recovery_target_action = 'promote'
EOF

aws rds modify-db-parameter-group \
    --db-parameter-group-name skyhigh-disp-dr \
    --parameters "ParameterName=recovery.conf,ParameterValue=$(base64 -w0 /tmp/recovery.conf)"

aws rds reboot-db-instance --db-instance-identifier skyhigh-disp-dr
aws rds wait db-instance-available --db-instance-identifier skyhigh-disp-dr

psql -h $PG_HOST -U admin -d postgres -c "SELECT pg_is_in_recovery();"
ШАГ 10: Проверка целостности PostgreSQL (5 минут)
sql
SELECT COUNT(*) FROM flight_plans WHERE status = 'ACTIVE' AND departure_time > NOW();
SELECT flight_id, status, updated_at FROM flights WHERE updated_at > NOW() - INTERVAL '1 hour' ORDER BY updated_at DESC LIMIT 50;
ВОССТАНОВЛЕНИЕ REDIS (КЭШ ПОЛЕТНЫХ ПЛАНОВ) - 15 МИНУТ
ШАГ 11: Восстановление Redis (10 минут)
bash
aws ec2 run-instances \
    --image-id ami-redis-prod-eu-central-1 \
    --instance-type r6g.large \
    --region eu-central-1 \
    --user-data "#!/bin/bash
aws s3 cp s3://skyhigh-backups/redis/latest.rdb /var/lib/redis/dump.rdb
systemctl restart redis"

REDIS_IP=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=redis-dr" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
ШАГ 12: Валидация Redis (5 минут)
bash
redis-cli -h $REDIS_IP DBSIZE
redis-cli -h $REDIS_IP KEYS "flight:*" | wc -l
redis-cli -h $REDIS_IP GET "flight:SKY-101" | jq '.'
ВОССТАНОВЛЕНИЕ MSSQL (MRO) - 2 ЧАСА
ШАГ 13: Восстановление MSSQL (60 минут)
bash
aws ec2 run-instances \
    --image-id ami-mssql-prod-eu-central-1 \
    --instance-type r5.2xlarge \
    --region eu-central-1

MSSQL_IP=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=mssql-dr" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

aws s3 cp s3://skyhigh-backups/mssql/full/backup_latest.bak /tmp/
aws s3 cp s3://skyhigh-backups/mssql/diff/backup_latest_diff.bak /tmp/

sqlcmd -S $MSSQL_IP -U SA -P 'SkyHigh2026!' -Q "
RESTORE DATABASE MRO FROM DISK = '/tmp/backup_latest.bak' WITH NORECOVERY;
RESTORE DATABASE MRO FROM DISK = '/tmp/backup_latest_diff.bak' WITH RECOVERY;
"
ШАГ 14: Проверка MRO (30 минут)
sql
SELECT part_number, quantity, warehouse FROM inventory WHERE part_type = 'ENGINE' AND quantity < 2;
SELECT aircraft_id, maintenance_due, days_remaining FROM maintenance_schedule WHERE days_remaining < 30;
DBCC CHECKDB('MRO') WITH NO_INFOMSGS;
ВОССТАНОВЛЕНИЕ KAFKA - 30 МИНУТ
ШАГ 15: Восстановление Kafka (20 минут)
bash
for i in {1..3}; do
    aws ec2 run-instances --image-id ami-kafka-prod-eu-central-1 --instance-type r5.large --region eu-central-1
done

aws s3 cp s3://skyhigh-backups/kafka/topics/ /tmp/kafka-backup/ --recursive

for topic_file in /tmp/kafka-backup/*.json; do
    topic=$(basename $topic_file .json)
    kafka-topics.sh --create --topic $topic --bootstrap-server $KAFKA_BROKERS \
        --partitions $(jq '.partitions' $topic_file)
done
ШАГ 16: Проверка Kafka (10 минут)
bash
kafka-topics.sh --list --bootstrap-server $KAFKA_BROKERS
kafka-consumer-groups.sh --bootstrap-server $KAFKA_BROKERS --list
ВОССТАНОВЛЕНИЕ S3 - 30 МИНУТ
ШАГ 17: Восстановление S3 (30 минут)
bash
aws s3 ls s3://skyhigh-satellite-data-eu/ --region eu-central-1 | head -20
aws s3 sync s3://skyhigh-satellite-data/ s3://skyhigh-satellite-data-eu/ --region eu-central-1
ФИНАЛЬНАЯ ПРОВЕРКА - 30 МИНУТ
ШАГ 18: Обновление балансировщиков (10 минут)
bash
ALB_ARN=$(aws elbv2 describe-load-balancers --names skyhigh-alb-dr --region eu-central-1 --query 'LoadBalancers[0].LoadBalancerArn' --output text)
TG_ARN=$(aws elbv2 describe-target-groups --names skyhigh-api-dr --region eu-central-1 --query 'TargetGroups[0].TargetGroupArn' --output text)

aws elbv2 modify-listener --listener-arn $LISTENER_ARN --region eu-central-1 --default-actions Type=forward,TargetGroupArn=$TG_ARN
ШАГ 19: Комплексная проверка API (10 минут)
bash
curl -X GET https://api.skyhigh.aero/booking/status/SKY-2026-12345 -H "Authorization: Bearer $API_TOKEN" | jq '.'
curl -X GET https://disp.skyhigh.aero/flights/active -H "Authorization: Bearer $API_TOKEN" | jq '.[] | {flight, status}'
curl -X GET https://mro.skyhigh.aero/inventory/search?part=engine -H "Authorization: Bearer $API_TOKEN" | jq '.'
ШАГ 20: Мониторинг стабильности (10 минут)
bash
aws logs filter-log-events --log-group-name /skyhigh/application --filter-pattern "ERROR" --start-time $(date -d '30 min ago' +%s)000
./health_check.py --all-services --verbose
АЛЬТЕРНАТИВНЫЙ СЦЕНАРИЙ (ЕСЛИ БЭКАП ПОВРЕЖДЕН)
ШАГ 21: Восстановление из реплики
bash
EXPECTED_CHECKSUM=$(aws s3api head-object --bucket skyhigh-backups --key db2/full/backup_latest.db2 --query 'Metadata.checksum' --output text)
ACTUAL_CHECKSUM=$(sha256sum /tmp/backup_latest.db2 | awk '{print $1}')

if [ "$EXPECTED_CHECKSUM" != "$ACTUAL_CHECKSUM" ]; then
    db2 CONNECT TO SKYHIGH_DB HADR_PEER
    db2 HADR ROLE CHANGE
fi
ШАГ 22: Сбор логов для анализа (10 минут)
bash
aws s3 cp /var/log/skyhigh/ s3://skyhigh-incident-logs/$(date +%Y%m%d_%H%M%S)/ --recursive
aws ec2 create-snapshot --volume-id $VOLUME_ID --description "Post-DR recovery state"
ВРЕМЕННЫЕ МЕТРИКИ
Шаг	Описание	Время (мин)
1-3	Подтверждение инцидента + DNS	5
4-7	Восстановление DB2	15
8-10	Восстановление PostgreSQL	30
11-12	Восстановление Redis	15
13-14	Восстановление MSSQL	120
15-16	Восстановление Kafka	30
17	Восстановление S3	30
18-20	Переключение и проверка	30
ИТОГО		≤ 4 часа
text

## ФАЙЛ 04_Scripts/backup_db2.sh

```bash
#!/bin/bash
# Скрипт архивации логов DB2
# Запуск: Каждые 5 минут через cron

DB_NAME="SKYHIGH_DB"
S3_BUCKET="skyhigh-backups"
ARCHIVE_DIR="/db2/archivelogs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/var/log/backup/db2_backup_$TIMESTAMP.log"

exec > >(tee -a $LOG_FILE)
exec 2>&1

echo "Starting DB2 archive at $(date)"

# Проверка свободного места
FREE_SPACE=$(df /db2 | awk 'NR==2 {print int($4/1024/1024)}')
if [ $FREE_SPACE -lt 10 ]; then
    echo "ERROR: Low disk space (< 10 GB)"
    exit 1
fi

# Переключение логов
db2 "ARCHIVE LOG FOR DATABASE $DB_NAME"

# Сжатие и загрузка в S3
find $ARCHIVE_DIR -name "*.LOG" -mmin -5 | while read LOG_FILE; do
    gzip -c $LOG_FILE > /tmp/log.gz
    CHECKSUM=$(sha256sum /tmp/log.gz | awk '{print $1}')
    
    aws s3api put-object \
        --bucket $S3_BUCKET \
        --key "db2/archivelogs/$TIMESTAMP/$(basename $LOG_FILE).gz" \
        --body /tmp/log.gz \
        --object-lock-mode GOVERNANCE \
        --object-lock-retain-until-date "$(date -d '+7 days' --iso-8601=seconds)" \
        --metadata checksum=$CHECKSUM
    
    echo "Uploaded: $LOG_FILE (checksum: $CHECKSUM)"
    rm -f $LOG_FILE /tmp/log.gz
done

# Очистка старых логов
find $ARCHIVE_DIR -name "*.LOG" -mtime +2 -delete

echo "DB2 archive completed at $(date)"