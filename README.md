# Smart Library Front Desk Voice Agent

An asynchronous, AI-powered voice assistant framework designed to automate public library front-desk operations. The system combines semantic vector search, live database verification, automated reservations, and security guardrails to provide accurate, real-time assistance for library patrons.

---

## Key Features

- **Unified Semantic Vector Search**  
  Replaces traditional keyword-based search with MongoDB Atlas Vector Search using the `all-MiniLM-L6-v2` embedding model, enabling conceptual and topic-based book discovery.

- **Retrieval-Augmented Generation (RAG)**  
  Retrieves book descriptions directly from MongoDB and injects them into the LLM context, allowing the assistant to generate accurate, context-aware summaries.

- **Deterministic Response Generation**  
  Uses the LiveKit Gemini Realtime model with a temperature of **0.1** to improve factual consistency, reduce hallucinations, and ensure reliable responses.

- **Asynchronous High-Performance Architecture**  
  Built with **FastAPI**, **Motor (AsyncIOMotorClient)**, and **LiveKit's asynchronous event framework** for efficient, scalable request handling.

- **Transaction Guardrails**  
  Implements parameter grounding and validation to ensure secure reservation workflows and prevent invalid database operations.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Programming Language** | Python 3.12+ |
| **Voice Agent Framework** | LiveKit Agents SDK |
| **LLM** | Google Gemini Realtime (`gemini-3.1-flash-live-preview`) |
| **Embedding Model** | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Backend Framework** | FastAPI + Uvicorn |
| **Database** | MongoDB Atlas (Vector Search) |
| **Async Database Driver** | Motor |

---

## Prerequisites & Environment Setup

Create a `.env` file in the project's root directory and add the following environment variables:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

GEMINI_API_KEY=your_gemini_api_key

MONGO_URI=your_mongodb_atlas_connection_string
```

---

## MongoDB Atlas Vector Search Index Configuration

Create an **Atlas Vector Search Index** on the `books` collection and name it:

```text
vector_index
```

Use the following index configuration:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    }
  ]
}
```

---

## Running the Application

Activate your virtual environment (`.venv`) and run the following commands in separate terminal windows.

### 1. Seed the Database (First-Time Setup Only)

```bash
python seed_mongo.py
```

### 2. Start the FastAPI Backend

```bash
uvicorn main:app --reload
```

### 3. Launch the LiveKit Voice Agent

```bash
python agent.py dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **GET** | `/callers/{phone}` | Verify a registered caller account. |
| **GET** | `/books?q={query}` | Perform semantic book search using MongoDB Atlas Vector Search. |
| **GET** | `/reservations?phone={phone}` | Retrieve all active reservations for a caller. |
| **POST** | `/reservations` | Create a new book reservation. |
| **PATCH** | `/reservations/{reservation_id}` | Update an existing reservation. |
| **DELETE** | `/reservations/{reservation_id}` | Cancel a reservation and restore book availability. |
