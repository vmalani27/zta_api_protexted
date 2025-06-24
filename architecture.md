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
    - Now includes port knocking for enhanced security before requests
    - Implements nonce/session management to prevent replay attacks
    - Built with FastAPI for modern, async API handling
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
- 5000: FastAPI Client (ZTA API Gateway)
- 5002: PDP Server
- 5003: PEP Server
- 7000, 8000, 9000: Port knocking sequence for client authentication

### Service Communication
```
Client Request Flow:
Client (FastAPI) --[Port Knocking]--> PEP Client -> PEP Server -> PDP Server -> Protected Resource
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
5. Nonce/session management is used to prevent replay attacks

### 2. Network Security
- All internal communication is encrypted
- Network segmentation between components
- RADIUS authentication for network access
- TLS for all external communications
- Port knocking required before sensitive service requests

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

## Recent & Future Considerations
- Integration with external identity providers
- Enhanced monitoring and observability
- Additional security layers as needed
- Scalability improvements
- **Recent:** Port knocking, nonce/session management, FastAPI-based client, improved PDP/PEP integration

## Implemented Features

- **Keycloak-based Authentication:**  
  Centralized identity and access management using Keycloak, with persistent PostgreSQL storage.

- **FastAPI-based Client:**  
  The client gateway is implemented with FastAPI, providing modern async API handling.

- **Port Knocking:**  
  Sensitive service requests require a port knocking sequence (7000, 8000, 9000) for enhanced security before access is granted.

- **Nonce/Session Management:**  
  Nonce generation and session tracking are used to prevent replay attacks and ensure request freshness.

- **PEP/PDP Integration:**  
  The client communicates with a Policy Enforcement Point (PEP) and Policy Decision Point (PDP) for fine-grained access control.  
  - PEP enforces access policies and validates tokens.
  - PDP evaluates policies and makes access decisions.

- **Protected Resource Enforcement:**  
  Application resources are protected and require valid authentication and authorization for access.

- **Centralized Logging:**  
  All components log events centrally for monitoring and auditing.

- **Network Segmentation & Encryption:**  
  Internal communications are encrypted, and network segmentation is enforced between components.

- **High Availability:**  
  critical services like pep, pdp and client are hosted on docker containers

- **Backup & Recovery:**  
  Regular backups and disaster recovery procedures are in place