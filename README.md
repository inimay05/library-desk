# Smart Library Front Desk Voice Agent

**Luna** is a real-time voice assistant for a public library front desk. Callers can search the catalogue by topic, check their reservations, and reserve, reschedule or cancel books by speaking. Luna searches books semantically with MongoDB Atlas Vector Search, reads book summaries from the database, and checks the phone numbers it acts on against the transcript of the call.

Built with LiveKit Agents, Gemini Live, FastAPI, MongoDB Atlas and [saidso](https://github.com/KarthikRommula/saidso).

---

## How It Works

```text
Caller (voice) → LiveKit → Gemini Live (Luna) → function tools → FastAPI → MongoDB Atlas
                                   │
                                   └── call transcript → saidso (checks phone numbers)
```

Luna verifies the caller by phone number first, then uses six tools: `verify_caller`, `search_books`, `get_reservations`, `make_reservation`, `update_reservation` and `cancel_reservation`. Each tool calls the FastAPI backend, which reads and writes MongoDB Atlas.

---

## Key Features

- **Semantic Vector Search**  
  Replaces keyword search with MongoDB Atlas Vector Search using the `all-MiniLM-L6-v2` embedding model, so callers can find books by topic or idea instead of exact title.

- **Database-Grounded Summaries (RAG)**  
  Book descriptions are retrieved from MongoDB and passed into the model's context through the search tool. If a book has no stored description, the tool returns "No description provided" instead of leaving the model to fill the gap.

- **Grounded Phone Numbers**  
  The phone number used to verify a caller or make a reservation is checked against the transcript of what the caller actually said, using saidso. See [Reliability](#reliability).

- **Low-Temperature Responses**  
  Gemini Live runs at a temperature of **0.1** for more consistent answers.

- **Asynchronous Architecture**  
  Built with **FastAPI**, **Motor (AsyncIOMotorClient)** and **LiveKit's asynchronous event framework**.

---

## Reliability

A voice agent acts on what it hears, so a misheard or invented phone number could put a reservation on the wrong person's account. Luna uses [saidso](https://github.com/KarthikRommula/saidso), a grounding library by Karthik Rommula, to guard against this.

- The agent adds each turn of the conversation to a running transcript.
- Before `verify_caller` and `make_reservation` run, saidso checks that the phone number appears in what the caller said (`Policy.SPOKEN`).
- If it does not, the action is blocked, the agent is told to re-ask, and the decision is logged in the terminal.

### Limitations

- Only phone numbers are grounded in code. Book IDs and pickup dates are not.
- `update_reservation` and `cancel_reservation` are not guarded by saidso. Reservation IDs are protected only by the instructions in `agent.py`, which tell Luna to use IDs returned by `get_reservations`.
- Grounding is only as accurate as the speech transcription. If the transcript itself is wrong, a wrong number can still pass.
- The transcript is kept at module level, so the agent is designed for one call at a time.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Programming Language** | Python 3.12+ |
| **Voice Agent Framework** | LiveKit Agents SDK |
| **LLM** | Google Gemini Realtime (`gemini-3.1-flash-live-preview`) |
| **Grounding** | saidso |
| **Embedding Model** | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Backend Framework** | FastAPI + Uvicorn |
| **Database** | MongoDB Atlas (Vector Search) |
| **Async Database Driver** | Motor |

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the project's root directory:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

GEMINI_API_KEY=your_gemini_api_key

MONGO_URI=your_mongodb_atlas_connection_string
```

### 3. MongoDB Atlas Vector Search index

Create an **Atlas Vector Search Index** on the `books` collection and name it:

```text
vector_index
```

Use this configuration:

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

Activate your virtual environment (`.venv`) and run the following in separate terminal windows.

### 1. Seed the database (first-time setup only)

```bash
python seed_mongo.py
```

### 2. Start the FastAPI backend

```bash
uvicorn main:app --reload
```

### 3. Launch the LiveKit voice agent

```bash
python agent.py dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| **GET** | `/callers/{phone}` | Verify a registered caller account. |
| **GET** | `/books?q={query}` | Semantic book search using MongoDB Atlas Vector Search. |
| **GET** | `/reservations?phone={phone}` | Retrieve all active reservations for a caller. |
| **POST** | `/reservations` | Create a new book reservation. |
| **PATCH** | `/reservations/{reservation_id}` | Update an existing reservation. |
| **DELETE** | `/reservations/{reservation_id}` | Cancel a reservation and restore book availability. |
