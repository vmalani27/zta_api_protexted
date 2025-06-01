# Zero Trust Architecture API

This API implements a Zero Trust Architecture for an educational institution, managing students, teachers, hostel wardens, and administrators.

## Features

- Role-based access control (RBAC)
- Secure authentication and authorization
- Student management (personal, academic, and hostel information)
- Teacher access to academic information
- Hostel warden access to hostel information
- Admin full access control

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
DATABASE_URL=sqlite:///./zta.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login to get access token

### Users
- `POST /api/v1/users` - Create new user (Admin only)
- `GET /api/v1/users/me` - Get current user info
- `GET /api/v1/users` - List all users (Admin only)

### Students
- `POST /api/v1/students` - Create new student (Admin only)
- `GET /api/v1/students` - List all students (Teachers/Wardens can see relevant info)
- `GET /api/v1/students/{student_id}` - Get student details
- `PUT /api/v1/students/{student_id}` - Update student info (Role-based field updates)
- `DELETE /api/v1/students/{student_id}` - Delete student (Admin only)

### Teachers
- `POST /api/v1/teachers` - Create new teacher (Admin only)
- `GET /api/v1/teachers` - List all teachers (Admin/Teachers)
- `GET /api/v1/teachers/{teacher_id}` - Get teacher details
- `PUT /api/v1/teachers/{teacher_id}` - Update teacher info (Admin only)
- `DELETE /api/v1/teachers/{teacher_id}` - Delete teacher (Admin only)

### Hostels
- `POST /api/v1/hostels` - Create new hostel (Admin only)
- `GET /api/v1/hostels` - List all hostels (Admin/Wardens)
- `GET /api/v1/hostels/{hostel_id}` - Get hostel details
- `PUT /api/v1/hostels/{hostel_id}` - Update hostel info (Admin only)
- `DELETE /api/v1/hostels/{hostel_id}` - Delete hostel (Admin only)

### Wardens
- `POST /api/v1/wardens` - Create new warden (Admin only)
- `GET /api/v1/wardens` - List all wardens (Admin/Wardens)
- `GET /api/v1/wardens/{warden_id}` - Get warden details
- `PUT /api/v1/wardens/{warden_id}` - Update warden info (Admin only)
- `DELETE /api/v1/wardens/{warden_id}` - Delete warden (Admin only)

## Access Control

The API implements role-based access control with the following roles:
- **Admin**: Full access to all endpoints and operations
- **Teacher**: Access to academic information and student academic records
- **Warden**: Access to hostel information and student hostel records
- **Student**: Limited access to personal information

## Project Structure

```
zta_api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── api.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   │   └── models.py
│   │   ├── schemas/
│   │   │   └── schemas.py
│   │   └── main.py
│   ├── alembic/
│   ├── requirements.txt
│   └── README.md
```

# Keycloak with PostgreSQL Docker Setup

This setup uses Docker Compose to run Keycloak with PostgreSQL using Bitnami's official images.

## Prerequisites

- Docker
- Docker Compose

## Configuration

The setup includes:

- Keycloak 24.x
- PostgreSQL 16.x
- Persistent volume for PostgreSQL data
- Network configuration for service communication

Default credentials:
- Keycloak Admin:
  - Username: `admin`
  - Password: `admin123`
- PostgreSQL:
  - Username: `bn_keycloak`
  - Password: `bitnami1234`
  - Database: `bitnami_keycloak`

## Running the Setup

1. Start the services:
```bash
docker-compose up -d
```

2. Access Keycloak:
- Admin Console: http://localhost:8080/admin
- HTTP API: http://localhost:8080
- HTTPS API: https://localhost:8443

## Stopping the Setup

To stop the services:
```bash
docker-compose down
```

To stop and remove volumes (this will delete all data):
```bash
docker-compose down -v
```

## Security Notes

For production use:
1. Change all default passwords
2. Use proper TLS certificates
3. Configure proper network security
4. Use environment variables or Docker secrets for sensitive data
5. Consider using a managed database service instead of the PostgreSQL container 