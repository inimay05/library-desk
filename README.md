# Smart Library Front Desk Voice Agent

An asynchronous, AI-powered voice assistant framework designed to handle public library front-desk operations. The system features semantic vector search, live database verification, automated reservations, and robust security guardrails to streamline caller interactions seamlessly.

---

## Key Features

* Unified Semantic Vector Search: Replaced traditional keyword-based matching with a dense vector search pipeline via MongoDB Atlas, utilizing the all-MiniLM-L6-v2 embedding model for conceptual, topic-based book discovery.
* Retrieval-Augmented Generation (RAG): Dynamically injects book descriptions pulled from the cloud database straight into the LLM context, enabling real-time, highly contextual book summarization.
* Deterministic Configuration Optimization: The LiveKit Gemini Realtime model operates at a strict temperature of 0.1, guaranteeing high precision, structural factual reliability, and preventing hallucinated database records.
* Asynchronous High-Performance Architecture: Completely built using FastAPI, Motor (AsyncIOMotorClient), and LiveKit's async event loop framework.
* Transaction Guardrails: Out-of-the-box parameter grounding integration ensuring secure data-handling workflows.

---

## Tech Stack

* Language: Python 3.12+
* Voice Agent Infrastructure: LiveKit / LiveKit Agents SDK
* LLM Engine: Google Gemini Realtime Model (gemini-3.1-flash-live-preview)
* Vector Embeddings: Sentence-Transformers (all-MiniLM-L6-v2)
* Backend Framework: FastAPI / Uvicorn
* Database Engine: MongoDB Atlas (Cloud Vector Search Cluster)
* Async Database Driver: Motor

---
## Prerequisites & Environment Setup

Create a `.env` file in your root directory containing your API credentials and database URI strings:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=your_mongodb_atlas_connection_string

# MongoDB Atlas Vector Search Index Configuration
To execute semantic search queries successfully, define the following Atlas Search Index on your books collection and name it vector_index:

JSON
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

---

## How to Run the System

To launch the complete live agent platform locally, activate your virtual environment (.venv) and start the following processes across separate terminal windows:

1. Seed the Database (First-time setup only)
python seed_mongo.py
2. Start the FastAPI Backend Server
uvicorn main:app --reload
3. Launch the LiveKit Voice Worker Node
python agent.py dev

---

## API Endpoints Summary (main.py)

* GET /callers/{phone} — Verifies registered caller accounts.
* GET /books?q={query} — Unified entry point running the internal Atlas Vector Search query matrix.
* GET /reservations?phone={phone} — Fetches active bookings mapping to a customer number.
* POST /reservations — Reserves an available text item, mapping state transitions in the database collections.
* PATCH /reservations/{reservation_id} — Modifies item collection dates.
* DELETE /reservations/{reservation_id} — Atomically cancels an active booking state and restores product availability.
