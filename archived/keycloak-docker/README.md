# Keycloak Docker Setup

This setup provides a complete Keycloak installation with PostgreSQL using Docker Compose.

## Prerequisites

- Docker Engine (version 20.10.0 or later)
- Docker Compose (version 2.0.0 or later)

## Quick Start

1. Navigate to the keycloak-docker directory:
```bash
cd keycloak-docker
```

2. Start the services:
```bash
docker-compose up -d
```

3. Wait for the services to start (this may take a few minutes on first run)

4. Access Keycloak:
- Admin Console: http://localhost:8080/admin
- HTTP API: http://localhost:8080
- HTTPS API: https://localhost:8443

## Default Credentials

### Keycloak Admin
- Username: `admin`
- Password: `admin123`

### PostgreSQL
- Username: `bn_keycloak`
- Password: `bitnami1234`
- Database: `bitnami_keycloak`

## Configuration Details

### Keycloak Configuration
- HTTP Port: 8080
- HTTPS Port: 8443
- Proxy Mode: edge
- Database: PostgreSQL

### PostgreSQL Configuration
- Port: 5432 (internal)
- Persistent Volume: postgresql_data
- Health Check: Enabled

## Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### Restart Services
```bash
docker-compose restart
```

### Remove All Data (Including Volumes)
```bash
docker-compose down -v
```

## Security Recommendations

For production use:

1. Change all default passwords
2. Use environment variables for sensitive data:
   ```bash
   export KEYCLOAK_ADMIN_PASSWORD=your_secure_password
   export POSTGRESQL_PASSWORD=your_secure_password
   ```

3. Configure proper TLS certificates
4. Use Docker secrets for sensitive data
5. Consider using a managed database service
6. Implement proper network security
7. Regular backups of the PostgreSQL data

## Troubleshooting

### Common Issues

1. **Keycloak fails to start**
   - Check PostgreSQL logs: `docker-compose logs postgresql`
   - Ensure PostgreSQL is healthy: `docker-compose ps postgresql`

2. **Database connection issues**
   - Verify network connectivity: `docker network inspect keycloak-docker_keycloak-network`
   - Check PostgreSQL logs for connection errors

3. **Port conflicts**
   - Ensure ports 8080 and 8443 are not in use
   - Modify ports in docker-compose.yml if needed

### Logs

View service logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs keycloak
docker-compose logs postgresql
```

## Backup and Restore

### Backup PostgreSQL Data
```bash
docker-compose exec postgresql pg_dump -U bn_keycloak bitnami_keycloak > backup.sql
```

### Restore PostgreSQL Data
```bash
docker-compose exec -T postgresql psql -U bn_keycloak bitnami_keycloak < backup.sql
``` 