from fastapi import FastAPI
from contextlib import asynccontextmanager # For lifespan events in newer FastAPI

from app.db.database import create_db_and_tables # Async version
from app.routers import users, groups, expenses # Async routers

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
    lifespan=lifespan # Use the lifespan context manager
)

# Include routers
app.include_router(users.router, prefix="/api/v1") # Example prefix
app.include_router(groups.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Expense Tracker API!"}

# Example of adding a simple middleware for basic error handling or logging (optional)
# from fastapi import Request, Response
# from fastapi.responses import JSONResponse
# @app.middleware("http")
# async def basic_error_middleware(request: Request, call_next):
#     try:
#         response = await call_next(request)
#         return response
#     except Exception as e:
#         # Log the exception e
#         # In a real app, be careful about sending internal error details to client
#         return JSONResponse(
#             status_code=500,
#             content={"message": "An internal server error occurred.", "error_detail": str(e)},
#         )
