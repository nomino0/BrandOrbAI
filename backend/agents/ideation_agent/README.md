# Business Idea Q&A API Documentation (MAX)

A FastAPI-based service for interactive business idea questioning and answering using AI-powered question generation, keyword suggestions, and answer validation.

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for this API.

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/init` | Initialize a new Q&A session |
| POST | `/respond` | Submit an answer to any question |
| POST | `/suggest-answer` | Generate suggested answer using keywords |
| GET | `/keywords/{session_id}/{question_index}` | Get keywords for a specific question |
| POST | `/reset` | Reset questions after a specific index |
| GET | `/session/{session_id}` | Get current session state |
| GET | `/summary/{session_id}` | Generate a comprehensive summary of the analysis |
| DELETE | `/session/{session_id}` | Delete a session |
| GET | `/` | API information and endpoint list |

---

## Detailed Endpoint Documentation

### 1. Initialize Session

**POST** `/init`

Initialize a new Q&A session with a business idea description and provided session ID.

**Request Body:**
```json
{
  "session_id": "your-session-id-here",
  "description": "My business idea description here"
}
```

**Response:**
```json
{
  "session_id": "your-session-id-here",
  "description": "My business idea description here",
  "questions": [
    {
      "question": "What is your target market?",
      "response": null,
      "keywords": null,
      "is_satisfactory": false,
      "satisfaction_reason": null
    }
  ]
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/init" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id-here",
    "description": "A mobile app for food delivery in small towns"
  }'
```

---

### 2. Submit Answer

**POST** `/respond`

Submit an answer to any question by its index. The system will check if the answer is satisfactory and generate the next question if all current questions are answered satisfactorily.

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "question_index": 0,
  "response": "Your answer here"
}
```

**Response:**
```json
{
  "question": "What is your revenue model?",
  "has_more_questions": true,
  "question_satisfaction": {
    "is_satisfactory": true,
    "reason": "The answer provides specific details about the target market"
  }
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_index": 0,
    "response": "Small town residents aged 25-45 who want food delivery options"
  }'
```

---

### 3. Get Keywords

**GET** `/keywords/{session_id}/{question_index}`

Get AI-generated keywords that could help answer a specific question. These keywords can be used with the suggest endpoint.

**Path Parameters:**
- `session_id`: The session UUID
- `question_index`: The index of the question (0-based)

**Response:**
```json
{
  "keywords": [
    "target demographics",
    "market size",
    "customer personas",
    "geographic location"
  ]
}
```

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/keywords/your-session-id/0"
```

---

### 4. Generate Suggested Answer

**POST** `/suggest-answer`

Generate a suggested answer using selected keywords for any question by index.

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "question_index": 0,
  "selected_keywords": [
    "target demographics",
    "small towns",
    "market size"
  ]
}
```

**Response:**
```json
{
  "answer": "The target market consists of residents in small towns with populations between 5,000-25,000, primarily focusing on working professionals aged 25-45 who value convenience and have disposable income for food delivery services."
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/suggest" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "question_index": 0,
    "selected_keywords": ["target demographics", "small towns", "market size"]
  }'
```

---

### 5. Get Session State

**GET** `/session/{session_id}`

Retrieve the current state of a session, including all questions, answers, and their satisfaction status.

**Path Parameters:**
- `session_id`: The session UUID

**Response:**
```json
{
  "session_id": "uuid-string",
  "description": "A mobile app for food delivery in small towns",
  "questions": [
    {
      "question": "What is your target market?",
      "response": "Small town residents aged 25-45",
      "keywords": ["target demographics", "market size"],
      "is_satisfactory": true,
      "satisfaction_reason": "Provides clear demographic details"
    },
    {
      "question": "What is your revenue model?",
      "response": null,
      "keywords": null,
      "is_satisfactory": false,
      "satisfaction_reason": null
    }
  ]
}
```

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/session/your-session-id"
```

---

### 6. Reset Questions

**POST** `/reset`

Remove all questions after a specific index. Useful for backtracking and exploring different question paths.

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "index": 1
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "description": "A mobile app for food delivery in small towns",
  "questions": [
    {
      "question": "What is your target market?",
      "response": "Small town residents aged 25-45",
      "keywords": ["target demographics", "market size"],
      "is_satisfactory": true,
      "satisfaction_reason": "Provides clear demographic details"
    }
  ]
}
```

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/reset" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "index": 1
  }'
```

---

### 7. Generate Summary

**GET** `/summary/{session_id}`

Generate a comprehensive summary of the business idea analysis based on all answered questions.

**Path Parameters:**
- `session_id`: The session UUID

**Response:**
```json
{
  "summary": "string"
}
```

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/summary/your-session-id"
```

**Example Response:**
```json
{
  "summary": "This business idea focuses on a mobile app for food delivery in small towns. The target market consists of residents aged 25-45 who value convenience and have disposable income. The revenue model is based on a commission from restaurant partners and delivery fees. Key challenges include managing delivery logistics in smaller areas and building trust with local restaurants."
}
```

---

### 8. Delete Session

**DELETE** `/session/{session_id}`

Permanently delete a session and all its data.

**Path Parameters:**
- `session_id`: The session UUID

**Response:**
```json
{
  "message": "Session deleted successfully"
}
```

**Example Usage:**
```bash
curl -X DELETE "http://localhost:8000/session/your-session-id"
```

---

## Typical Workflow

### 1. Start a New Session
```bash
# Initialize with business idea
POST /init
{
  "description": "A subscription box service for pet owners"
}
```

### 2. Get Keywords for Current Question
```bash
# Get suggested keywords
GET /keywords/{session_id}/0
```

### 3. Generate or Submit Answer
```bash
# Option A: Generate suggested answer
POST /suggest
{
  "session_id": "uuid",
  "question_index": 0,
  "selected_keywords": ["pet owners", "subscription model", "target market"]
}

# Option B: Submit your own answer
POST /respond
{
  "session_id": "uuid",
  "question_index": 0,
  "response": "Pet owners with disposable income who want convenience"
}
```

### 4. Continue Until Complete
```bash
# Check session state
GET /session/{session_id}

# Answer more questions as they're generated
POST /respond
```

### 5. Edit Previous Answers (if needed)
```bash
# Edit any previous answer by index
POST /respond
{
  "session_id": "uuid",
  "question_index": 0,  # Edit first question's answer
  "response": "Updated answer with more details"
}
```

---

## Error Responses

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid question index or missing data |
| 404 | Not Found - Session not found |
| 422 | Validation Error - Invalid request format |

### Example Error Response
```json
{
  "detail": "Session not found"
}
```

---

## Important Notes

### Session Management
- Sessions are stored in memory and will be lost when the server restarts
- Each session has a unique UUID identifier
- No automatic session cleanup is implemented
- Session IDs must be unique - attempting to use an existing session ID will result in a 400 error

### Question Indexing
- Questions are zero-indexed (first question is index 0)
- You can edit answers to any question at any time using its index
- Editing earlier answers may affect the satisfaction status

### AI Behavior
- The system generates new questions only when all current questions have satisfactory answers
- Keywords are generated contextually based on the business idea and previous Q&A
- Satisfaction checking helps ensure comprehensive answers before proceeding

### Best Practices
- Always check the session state before making requests
- Use keywords to get better suggested answers
- Consider resetting questions if you want to explore different paths
- Save important session IDs as they cannot be recovered if lost
- When initializing a session, ensure the provided session ID is unique
