# API Documentation for Interview Evaluator

This document provides comprehensive documentation for the Interview Evaluator API endpoints, request/response formats, and authentication requirements.

## Base URL

```
https://api.interview-evaluator.app
```

For local development:

```
http://localhost:8000
```

## Authentication

All endpoints except `/health` require JWT authentication using a Bearer token. Obtain a token by signing in through the `/auth/login` endpoint.

### Headers

Include the following headers in your requests:

```
Authorization: Bearer <your_token>
```

## API Endpoints

### Health Check

Check the health status of the API and its dependencies.

**Endpoint**: `GET /health`

**Authentication**: None

**Response Example**:

```json
{
  "status": "ok",
  "timestamp": "2023-04-17T19:20:30.123456",
  "dependencies": {
    "supabase": "connected",
    "sentry": "configured",
    "langsmith": "configured"
  }
}
```

### Authentication

#### Login

Authenticate a user and get a JWT token.

**Endpoint**: `POST /auth/login`

**Authentication**: None

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response Example**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "expires_in": 3600
}
```

#### Sign Up

Register a new user.

**Endpoint**: `POST /auth/signup`

**Authentication**: None

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response Example**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "expires_in": 3600
}
```

### Evaluation

#### Upload Transcript

Upload an interview transcript for evaluation.

**Endpoint**: `POST /upload`

**Authentication**: Required

**Request**: Multipart form data with a file attachment

**Response Example**:

```json
{
  "message": "Transcript uploaded successfully, processing started",
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_name": "John Smith",
  "filename": "interview_transcript.txt",
  "status": "uploaded"
}
```

#### Get Evaluation Status

Check the status of an evaluation.

**Endpoint**: `GET /status/{interview_id}`

**Authentication**: Required

**Response Example**:

```json
{
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "candidate_name": "John Smith",
  "created_at": "2023-04-17T19:20:30.123456",
  "updated_at": "2023-04-17T19:22:30.123456"
}
```

Status values:
- `uploaded`: Initial state after upload
- `processing`: Evaluation in progress
- `evaluated`: Evaluation completed
- `error`: Error occurred during processing

#### Get Evaluation Results

Retrieve the results of a completed evaluation.

**Endpoint**: `GET /results/{interview_id}`

**Authentication**: Required

**Response Example**:

```json
{
  "status": "success",
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_name": "John Smith",
  "interview_date": "2023-04-17T19:20:30.123456",
  "overall_score": 7.5,
  "summary": "John Smith demonstrated strong technical knowledge in data science concepts...",
  "strengths": [
    "Statistical analysis",
    "Machine learning algorithms",
    "Communication skills"
  ],
  "weaknesses": [
    "SQL optimization",
    "Time management"
  ],
  "criteria_evaluations": [
    {
      "criterion": "Technical Knowledge",
      "score": 8,
      "justification": "Demonstrated strong understanding of statistical concepts and machine learning algorithms.",
      "supporting_quotes": [
        "I would approach this classification problem using a Random Forest because...",
        "The key difference between supervised and unsupervised learning is..."
      ]
    },
    {
      "criterion": "Problem Solving",
      "score": 7,
      "justification": "Showed good analytical thinking but occasionally made incorrect assumptions.",
      "supporting_quotes": [
        "To optimize this query, I would first look at the execution plan...",
        "The time complexity of this algorithm would be O(n log n) because..."
      ]
    }
  ]
}
```

#### Get All Evaluations

Retrieve all evaluations for the authenticated user.

**Endpoint**: `GET /evaluations?limit=20&offset=0`

**Authentication**: Required

**Query Parameters**:
- `limit`: Maximum number of evaluations to return (default: 20)
- `offset`: Offset for pagination (default: 0)

**Response Example**:

```json
[
  {
    "interview_id": "550e8400-e29b-41d4-a716-446655440000",
    "candidate_name": "John Smith",
    "interview_date": "2023-04-17T19:20:30.123456",
    "overall_score": 7.5,
    "summary": "John Smith demonstrated strong technical knowledge...",
    "strengths": ["Statistical analysis", "..."],
    "weaknesses": ["SQL optimization", "..."],
    "criteria_evaluations": [...]
  },
  {
    "interview_id": "660e8400-e29b-41d4-a716-446655440000",
    "candidate_name": "Jane Doe",
    "interview_date": "2023-04-16T15:20:30.123456",
    "overall_score": 8.2,
    "summary": "Jane Doe excelled in both technical knowledge and problem solving...",
    "strengths": ["Python programming", "..."],
    "weaknesses": ["Database design", "..."],
    "criteria_evaluations": [...]
  }
]
```

#### Evaluate Transcript Directly

Synchronously evaluate a transcript.

**Endpoint**: `POST /evaluate`

**Authentication**: Required

**Request Body**:

```json
{
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_name": "John Smith",
  "transcript_path": "/path/to/transcript.txt"
}
```

**Response**: Same format as `GET /results/{interview_id}`

### Monitoring

#### Get Monitoring Metrics

Retrieve system monitoring metrics.

**Endpoint**: `GET /monitoring/metrics?days=7`

**Authentication**: Required (admin)

**Query Parameters**:
- `days`: Number of days of data to include (default: 7)

**Response Example**:

```json
{
  "status": "success",
  "timestamp": "2023-04-17T19:20:30.123456",
  "langsmith_metrics": {
    "total_runs": 120,
    "successful_runs": 112,
    "error_runs": 8,
    "success_rate": 0.933,
    "average_latency_seconds": 12.5,
    "run_types": {
      "chain": 80,
      "llm": 40
    }
  },
  "database_metrics": {
    "total_interviews": 150,
    "total_evaluations": 130,
    "usage_statistics": {
      "total_interviews": 45,
      "by_status": {
        "uploaded": 5,
        "processing": 2,
        "evaluated": 36,
        "error": 2
      },
      "daily_counts": {
        "2023-04-17": 8,
        "2023-04-16": 12,
        "2023-04-15": 5,
        "2023-04-14": 7,
        "2023-04-13": 4,
        "2023-04-12": 5,
        "2023-04-11": 4
      }
    }
  }
}
```

## Error Handling

All endpoints follow a standard error response format:

```json
{
  "status": "error",
  "message": "A descriptive error message",
  "detail": "Optional detailed error information"
}
```

Common HTTP status codes:

- `200 OK`: Request successful
- `202 Accepted`: Request accepted for processing
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict or invalid state transition
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are limited to:
- 10 requests per minute for `/auth/*` endpoints
- 60 requests per minute for other endpoints

Rate limit headers in responses:
- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests for the current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit window resets

## Webhook Notifications

The API can send webhook notifications for evaluation events. Configure webhooks in the user settings.

Events:
- `evaluation.started`: Evaluation has begun
- `evaluation.completed`: Evaluation has been completed
- `evaluation.error`: Error occurred during evaluation

Webhook payload example:

```json
{
  "event": "evaluation.completed",
  "interview_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2023-04-17T19:20:30.123456",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "data": {
    "candidate_name": "John Smith",
    "overall_score": 7.5
  }
}
```

## SDK and Client Libraries

Official SDKs are available for:
- JavaScript/TypeScript (frontend and Node.js)
- Python

Example usage (TypeScript):

```typescript
import { InterviewEvaluatorClient } from '@interview-evaluator/sdk';

const client = new InterviewEvaluatorClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.interview-evaluator.app'
});

// Upload and evaluate a transcript
const result = await client.evaluateTranscript({
  file: transcriptFile, // File object
  candidateName: 'John Smith'
});

console.log(result.overallScore);
```

Example usage (Python):

```python
from interview_evaluator import Client

client = Client(
    api_key='your_api_key',
    base_url='https://api.interview-evaluator.app'
)

# Upload and evaluate a transcript
result = client.evaluate_transcript(
    file_path='/path/to/transcript.txt',
    candidate_name='John Smith'
)

print(result.overall_score)
```