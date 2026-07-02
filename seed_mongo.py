import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

books = [
    {"id": "B001", "title": "Python Crash Course", "available": True,
     "description": "A beginner's guide to learning Python programming from scratch."},
    {"id": "B002", "title": "Clean Code", "available": False,
     "description": "How to write readable, maintainable, and professional software."},
    {"id": "B003", "title": "Deep Learning", "available": True,
     "description": "Neural networks, AI models, and machine learning fundamentals."},
    {"id": "B004", "title": "The Pragmatic Programmer", "available": True,
     "description": "Career advice and best practices for becoming a better developer."},
    {"id": "B005", "title": "Atomic Habits", "available": False,
     "description": "Building good daily routines and breaking bad habits for self improvement."},
]

callers = [
    {"phone": "9876543210", "name": "Mini", "active_reservations": ["R001"]},
    {"phone": "9123456789", "name": "Amy", "active_reservations": ["R002"]},
    {"phone": "9000000001", "name": "Mark", "active_reservations": []},
]

reservations = [
    {"id": "R001", "caller_phone": "9876543210", "book_id": "B002",
     "book_title": "Clean Code", "pickup_date": "2026-07-10", "status": "active"},
    {"id": "R002", "caller_phone": "9123456789", "book_id": "B005",
     "book_title": "Atomic Habits", "pickup_date": "2026-07-12", "status": "active"},
]

async def seed():
    client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
    db = client["library_db"]

    # Clear existing
    await db.books.delete_many({})
    await db.callers.delete_many({})
    await db.reservations.delete_many({})

    # Insert books with embeddings
    for book in books:
        book["embedding"] = model.encode(book["description"]).tolist()
    await db.books.insert_many(books)
    print(f"✅ Inserted {len(books)} books with embeddings")

    await db.callers.insert_many(callers)
    print(f"✅ Inserted {len(callers)} callers")

    await db.reservations.insert_many(reservations)
    print(f"✅ Inserted {len(reservations)} reservations")

    print("✅ Seed complete! Check Atlas Collections.")

asyncio.run(seed())