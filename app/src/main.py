from fastapi import FastAPI
from contextlib import asynccontextmanager  # For lifespan events in newer FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import create_db_and_tables
from src.routers import users, groups, expenses


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    # In a production app, you might use Alembic for migrations instead of create_all.
    print("Application startup: Creating database tables...")
    await create_db_and_tables()
    print("Database tables created (if they didn't exist).")
    yield
    # Shutdown: Any cleanup can go here
    print("Application shutdown.")


app = FastAPI(
    title="Expense Tracker API",
    description="API for managing expenses, users, and groups.",
    version="0.1.0",
    lifespan=lifespan,  # Use the lifespan context manager
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")  # Example prefix
app.include_router(groups.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Expense Tracker API!"}
