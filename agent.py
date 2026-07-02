import httpx
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, JobContext
from livekit.plugins.google import beta as google
from saidso import grounded, Policy, Transcript, AttestationLog, call_context, enable_pretty_logging

load_dotenv()
enable_pretty_logging()

FASTAPI_URL = "http://127.0.0.1:8000"

_transcript = Transcript()
_audit = AttestationLog()


@function_tool
async def search_books(query: str) -> str:
    """Search for books in the library catalog by title or topic."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{FASTAPI_URL}/books", params={"q": query})
            data = r.json()
            if not data["results"]:
                return "No books found matching that search."
            
            # Updated to pass the custom description text straight from MongoDB to Luna
            books = [
                f"{b['title']} (ID: {b['id']}) - {'Available' if b['available'] else 'Not available'}. Summary: {b.get('description', 'No description provided.')}"
                for b in data["results"]
            ]
            return "Found these books: " + " | ".join(books)
        except Exception as e:
            return f"Error searching books: {str(e)}"


@function_tool
async def get_reservations(caller_phone: str) -> str:
    """Get all active reservations for a verified caller by phone number."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{FASTAPI_URL}/reservations",
                params={"phone": caller_phone}
            )
            data = r.json()
            if not data["reservations"]:
                return "No active reservations found for this caller."
            result = []
            for res in data["reservations"]:
                result.append(
                    f"ID: {res['id']}, Book: {res['book_title']}, Pickup: {res['pickup_date']}"
                )
            return "Active reservations: " + " | ".join(result)
        except Exception as e:
            return f"Error fetching reservations: {str(e)}"


@function_tool
async def verify_caller(phone: str) -> str:
    """Verify if a caller exists in the system by their phone number."""
    @grounded(phone=Policy.SPOKEN)
    def _guarded(phone: str):
        return phone

    with call_context(_transcript, ledger=_audit):
        result = _guarded(phone=phone)

    if getattr(result, "blocked", False):
        return result.message

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{FASTAPI_URL}/callers/{phone}")
            if r.status_code == 404:
                return "Caller not found. This number is not registered."
            data = r.json()
            return f"Caller verified: {data['name']}. Reservations: {data['active_reservations']}"
        except Exception as e:
            return f"Error verifying caller: {str(e)}"


@function_tool
async def make_reservation(caller_phone: str, book_id: str, pickup_date: str) -> str:
    """Make a book reservation for a verified caller."""
    @grounded(
        caller_phone=Policy.SPOKEN
    )
    def _guarded(caller_phone, book_id, pickup_date):
        return caller_phone, book_id, pickup_date

    with call_context(_transcript, ledger=_audit):
        result = _guarded(
            caller_phone=caller_phone,
            book_id=book_id,
            pickup_date=pickup_date
        )

    if getattr(result, "blocked", False):
        return result.message

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{FASTAPI_URL}/reservations",
                json={
                    "caller_phone": caller_phone,
                    "book_id": book_id,
                    "pickup_date": pickup_date
                }
            )
            if r.status_code == 400:
                return "Sorry, that book is not available for reservation."
            if r.status_code == 404:
                return "Book not found in our system."
            data = r.json()
            return f"Reservation confirmed! ID: {data['reservation']['id']}, Book: {data['reservation']['book_title']}, Pickup: {data['reservation']['pickup_date']}"
        except Exception as e:
            return f"Error making reservation: {str(e)}"


@function_tool
async def update_reservation(reservation_id: str, new_pickup_date: str) -> str:
    """Update the pickup date of an existing reservation."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.patch(
                f"{FASTAPI_URL}/reservations/{reservation_id}",
                json={"pickup_date": new_pickup_date}
            )
            if r.status_code == 404:
                return "Reservation not found. Please check the reservation ID."
            data = r.json()
            return f"Reservation updated. New pickup date: {data['reservation']['pickup_date']}"
        except Exception as e:
            return f"Error updating reservation: {str(e)}"


@function_tool
async def cancel_reservation(reservation_id: str) -> str:
    """Cancel an existing reservation by its ID."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.delete(
                f"{FASTAPI_URL}/reservations/{reservation_id}"
            )
            if r.status_code == 404:
                return "Reservation not found. Please check the reservation ID."
            data = r.json()
            return f"Reservation cancelled successfully. Book '{data['book']}' is now available."
        except Exception as e:
            return f"Error cancelling reservation: {str(e)}"


class LibraryAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            You are Luna, a friendly and professional front desk assistant 
            at a public library. You communicate via voice only.

            STRICT RULES — never break these:
            1. ALWAYS call verify_caller first before doing anything else.
            2. NEVER confirm, create, update or cancel anything without 
               calling the appropriate tool first.
            3. NEVER make up book titles, availability, or reservation IDs.
            4. If a tool returns an error, tell the user honestly.
            5. If asked anything outside your scope, escalate to a human.
            6. Keep responses short and natural — this is a voice conversation.
            7. After completing any task, politely end the call.
            8. NEVER mention tools, functions, APIs, or system processes to the user.
            9. NEVER say things like "let me look that up", "checking the system",
               "running a search", or "calling a function".
            10. Speak as a real human receptionist would — naturally and conversationally.
            11. When a tool returns data, just speak the result naturally.
            12. When the user first speaks or greets you, immediately introduce 
                itself as Luna and ask for their name and phone number.
            13. Speak calmly and warmly — like a kind librarian would.
            14. Use a gentle, measured pace. Add natural pauses between sentences.
            15. If the user wants to update or cancel a reservation and does not 
                know their reservation ID, call get_reservations with their phone 
                number to look it up. NEVER proceed without a real reservation ID 
                from the tool.
            16. NEVER invent or guess a reservation ID. Only use IDs returned 
                by get_reservations or confirm_reservation tools.

            YOUR SCOPE:
            - Verifying callers
            - Searching books
            - Getting reservations
            - Making reservations
            - Updating pickup dates
            - Cancelling reservations
            - Escalating to a human when needed

            ISOLATE AND ESCALATE immediately if:
            - User asks for a human
            - You fail the same action twice
            - Request is outside your scope
            """,
            tools=[
                verify_caller,
                search_books,
                get_reservations,
                make_reservation,
                update_reservation,
                cancel_reservation,
            ]
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-3.1-flash-live-preview",
            voice="Kore",
            temperature=0.1
        ),
    )

    @session.on("conversation_item_added")
    def on_turn(event):
        msg = event.item
        if msg.role == "user" and msg.text_content:
            _transcript.add_user(msg.text_content)
        elif msg.role == "assistant" and msg.text_content:
            _transcript.add_agent(msg.text_content)

    await session.start(
        room=ctx.room,
        agent=LibraryAgent(),
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )