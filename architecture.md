# Zero Trust Architecture (ZTA) in Kubernetes

## Overview
This document outlines the structure and components of our Zero Trust Architecture implementation in Kubernetes. The architecture follows a microservices-based approach with multiple security layers and components.

## Core Components

### 1. Authentication Layer
- **Keycloak**
  - Primary Identity and Access Management (IAM) solution
  - Handles user authentication and authorization
  - Persistent storage using PostgreSQL
  - Exposed on ports 8080 (HTTP) and 8443 (HTTPS)
  - Located in `keycloak` namespace

### 2. Policy Enforcement Layer
- **PEP (Policy Enforcement Point) Components**
  - PEP Client
    - Handles initial request validation
    - Communicates with PEP Server
  - PEP Server
    - Enforces access policies
    - Communicates with PDP Server
  - PDP (Policy Decision Point) Server
    - Makes access control decisions
    - Evaluates policies against user context

### 3. Network Access Control
- **Network Controller**
  - Manages network-level access control
  - Integrates with FreeRADIUS for network authentication
  - Controls network segmentation

- **NAC (Network Access Control) Service**
  - Handles device authentication
  - Manages network access policies
  - Integrates with FreeRADIUS

### 4. Protected Resources
- **Protected Resource Service**
  - Represents the actual application resources
  - Enforces ZTA policies at the application level
  - Requires valid authentication and authorization

## Network Architecture

### Port Mappings
- 80: HTTP traffic
- 443: HTTPS traffic
- 8080: Keycloak HTTP
- 8443: Keycloak HTTPS
- 1812: RADIUS Authentication
- 1813: RADIUS Accounting

### Service Communication
```
Client Request Flow:
Client -> PEP Client -> PEP Server -> PDP Server -> Protected Resource
                                    |
                                    v
                              Keycloak (Auth)
```

## Security Considerations

### 1. Authentication Flow
1. User authenticates through Keycloak
2. Token is validated by PEP Client
3. PEP Server enforces policies
4. PDP Server makes final access decisions

### 2. Network Security
- All internal communication is encrypted
- Network segmentation between components
- RADIUS authentication for network access
- TLS for all external communications

### 3. Data Persistence
- Keycloak: PostgreSQL with 8Gi persistent storage
- Other services: Appropriate persistent storage as needed

## Deployment Structure

### Namespaces
- `keycloak`: Authentication services
- `default`: Core ZTA components
- `monitoring`: Observability tools (optional)

### Resource Requirements
- Each component has defined resource limits
- Persistent storage for stateful components
- Horizontal scaling capabilities where needed

## Monitoring and Logging
- Centralized logging for all components
- Metrics collection for performance monitoring
- Alerting for security events

## High Availability
- Keycloak: Multi-replica deployment
- Critical services: Multiple replicas
- Load balancing for external access

## Backup and Recovery
- Regular backups of Keycloak data
- State persistence for critical services
- Disaster recovery procedures

## Future Considerations
- Integration with external identity providers
- Enhanced monitoring and observability
- Additional security layers as needed
- Scalability improvements 