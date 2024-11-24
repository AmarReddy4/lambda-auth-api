# Lambda Auth API

Serverless API with custom JWT authorization built on AWS Lambda, API Gateway, and DynamoDB.

## Overview

This project implements a secure REST API using a custom Lambda authorizer for JWT-based authentication. Protected endpoints provide CRUD operations for user profiles stored in DynamoDB.

## Architecture

```
Client -> API Gateway -> Lambda Authorizer (JWT validation)
                      -> Users Lambda (CRUD operations) -> DynamoDB
```

### Components

- **Authorizer Function**: Custom Lambda authorizer that validates JWT tokens from the `Authorization` header and returns IAM policy documents
- **Users Function**: Protected Lambda handling user profile CRUD operations
- **DynamoDB Table**: Stores user profile data with on-demand billing

## Tech Stack

- Python 3.12
- AWS Lambda + API Gateway
- AWS DynamoDB
- PyJWT for token handling
- AWS SAM for infrastructure

## Getting Started

### Prerequisites

- Python 3.12+
- AWS SAM CLI
- AWS credentials configured

### Local Development

```bash
pip install -r requirements.txt

# Start local API
sam local start-api --parameter-overrides JwtSecret=your-dev-secret
```

### Deploy

```bash
sam build
sam deploy --guided
```

## API Endpoints

All endpoints require a valid JWT in the `Authorization` header:

```
Authorization: Bearer <token>
```

| Method | Path | Description |
|--------|------|-------------|
| GET | /users | List all user profiles |
| GET | /users/{userId} | Get a specific user profile |
| POST | /users | Create a new user profile |
| PUT | /users/{userId} | Update an existing profile |
| DELETE | /users/{userId} | Delete a user profile |

### Create User Request Body

```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "bio": "Software engineer"
}
```

## Token Format

JWTs include the following claims:

| Claim | Description |
|-------|-------------|
| sub | Subject (user ID) |
| email | User email |
| role | User role (default: "user") |
| iat | Issued at timestamp |
| exp | Expiration timestamp |

## License

MIT
