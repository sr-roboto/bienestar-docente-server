from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Database
from database import engine, Base
from models.user import UserDB
from models.community import CommunityPostDB
from models.mood import MoodEntryDB

# Routers
from routers.auth import router as auth_router, google_router
from routers.chat import router as chat_router
from routers.community import router as community_router
from routers.mood import router as mood_router

# MCP
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
import mcp.types as types

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Bienestar Docente API")

# CORS settings
from config import FRONTEND_URL

def clean_url(url):
    if not url: return None
    return url.rstrip('/')

cleaned_frontend_url = clean_url(FRONTEND_URL)
print(f"DEBUG: Configured FRONTEND_URL: {FRONTEND_URL}")
print(f"DEBUG: Cleaned FRONTEND_URL for CORS: {cleaned_frontend_url}")

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

if cleaned_frontend_url:
    origins.append(cleaned_frontend_url)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(google_router)
app.include_router(chat_router)
app.include_router(community_router)
app.include_router(mood_router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Bienestar Docente API"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_msg = traceback.format_exc()
    print(f"CRITICAL ERROR: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "debug": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


# --- MCP Server Implementation ---

mcp_server = Server("bienestar-docente-mcp")


@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_mood_stats",
            description="Get mood statistics for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The ID of the user"
                    }
                },
                "required": ["user_id"]
            }
        )
    ]


@mcp_server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[TextContent]:
    """Handle MCP tool calls."""
    if name == "get_mood_stats":
        user_id = arguments.get("user_id")
        # Simplified: would need DB session here
        return [TextContent(
            type="text",
            text=f"Mood stats for user {user_id}: Happy 60%, Neutral 30%, Sad 10%"
        )]
    else:
        raise ValueError(f"Unknown tool: {name}")


# --- MCP Server Implementation ---

mcp_server = Server("bienestar-docente-mcp")


@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools."""
    return [
        types.Tool(
            name="log_mood",
            description="Log a user's mood and optional note.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {"type": "string", "description": "The mood (happy, stressed, etc)"},
                    "note": {"type": "string", "description": "Optional note about the mood"}
                },
                "required": ["mood"]
            }
        ),
        types.Tool(
            name="get_latest_posts",
            description="Get the latest community posts.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        )
    ]


@mcp_server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle MCP tool calls."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        if name == "log_mood":
            mood = arguments.get("mood")
            note = arguments.get("note")
            if not mood:
                raise ValueError("Mood is required")
            
            # Use generic admin for MCP
            user = db.query(UserDB).first()
            user_id = user.id if user else None

            db_entry = MoodEntryDB(mood=mood, note=note, user_id=user_id)
            db.add(db_entry)
            db.commit()
            return [types.TextContent(type="text", text=f"Mood '{mood}' logged successfully.")]

        elif name == "get_latest_posts":
            posts = db.query(CommunityPostDB).order_by(CommunityPostDB.id.desc()).limit(5).all()
            text = "\n".join([f"- {p.author}: {p.content}" for p in posts])
            return [types.TextContent(type="text", text=f"Latest posts:\n{text}")]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    finally:
        db.close()


# SSE Endpoint for MCP
sse_transport = SseServerTransport("/sse")


@app.get("/sse")
async def handle_sse(request):
    """SSE endpoint for MCP."""
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


@app.post("/sse")
async def handle_sse_post(request):
    """Handle MCP POST messages."""
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

