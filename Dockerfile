FROM mysql:8.0
COPY app_db_backup.sql /docker-entrypoint-initdb.d/app_db_backup.sql