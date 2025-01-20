# PolarisAI Backend

Backend services for PolarisAI using FastAPI, MySQL, and Keycloak.

## Prerequisites
- Docker
- Docker Compose

## Setup

1. Clone the repository
```bash
git clone -b girish https://github.com/prowiz-analytics/polarisai-app-api
```

2. Create `.env` file
```env
MYSQL_ROOT_PASSWORD=rootpass
MYSQL_DATABASE=app_db
MYSQL_USER=app_user
MYSQL_PASSWORD=root
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin_password
```

3. Build and Start Services
```bash
# Clean build containers
docker-compose build --no-cache

# Start services in background
docker-compose up -d
```
4. Database Access
```bash
# Connect to MySQL
docker exec -it mysql-docker-mysql-1 mysql -u app_user -p
# Password: root
```

## Access Points

### Service URLs
- FastAPI: http://localhost:8000
- Keycloak: http://localhost:8080
- MySQL: localhost:3308


## Docker Operations

### Container Management
```bash
# View MySQL logs
docker-compose logs -f mysql

# Stop all services
docker-compose down
```

### Database Operations
```bash
# Backup database
docker exec mysql-docker-mysql-1 mysqldump -u root -prootpass app_db > app_db_backup.sql

# Restore database
docker cp app_db_backup.sql mysql-docker-mysql-1:/tmp/app_db_backup.sql
docker exec -it mysql-docker-mysql-1 mysql -u root -prootpass

# In MySQL prompt
use app_db;
source /tmp/app_db_backup.sql;
```  
