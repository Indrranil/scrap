# PolarisAI Backend

Backend services for PolarisAI using FastAPI, MySQL, and Keycloak.

## Prerequisites

- Docker
- Docker Compose

## Setup

1. Create .env file:
```env
MYSQL_ROOT_PASSWORD=rootpass
MYSQL_DATABASE=app_db
MYSQL_USER=app_user
MYSQL_PASSWORD=root
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin_password
```

2. Build containers (clean build):
```bash
docker-compose build --no-cache
```

3. Start services in background:
```bash
docker-compose up -d
```

4. Connect to MySQL:
```bash
docker exec -it mysql-docker-mysql-1 mysql -u app_user -p
# Enter password: root
```

## Service URLs

- FastAPI: http://localhost:8000
- Keycloak: http://localhost:8080
- MySQL: localhost:3308