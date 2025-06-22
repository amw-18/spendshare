from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # For serving static files
import os # For path joining
from contextlib import asynccontextmanager  # For lifespan events in newer FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.database import create_db_and_tables
from src.routers import users, groups, expenses, currencies, balances, conversion_rates, transactions, beta # Added beta
from src.config import settings

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
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,  # Use the lifespan context manager
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup for uploads
# This assumes 'main.py' is in 'app/src/' and 'uploads' directory is in 'app/uploads/'
# So, the path to 'app/uploads' from 'app/src/main.py' is '../uploads'
# If main.py is in 'app/', then path is 'uploads'
# Assuming CWD is /app (where Dockerfile is, and where app/src and app/uploads would be)
# So, "uploads" should resolve to "/app/uploads" if the app is run from /app.

# Let's make the path more robust by constructing it from the app's root.
# Assuming this script (main.py) is in app/src.
# Project root for backend files is 'app'.
# So 'app/uploads' is the target.
# Path from app/src/main.py to app/uploads is os.path.join(os.path.dirname(__file__), '..', 'uploads')
# However, FastAPI's StaticFiles directory path is usually relative to where the app is run, or an absolute path.

# If app is run from /app directory:
# Mount static files from the 'uploads' directory (which is /app/uploads)
# The UPLOAD_DIR_RECEIPTS in expenses.py creates "uploads/receipts" inside /app.
# So we serve the "uploads" directory.
# The URL will be /uploads/receipts/filename.ext

# Ensure the uploads directory exists at app startup (optional, but good practice)
# This path should correspond to where files are saved in expenses.py (i.e. app/uploads)
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True) # Create /app/uploads if not exists

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Include routers
app.include_router(users.router, prefix="/api/v1")  # Example prefix
app.include_router(groups.router, prefix="/api/v1")
app.include_router(expenses.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1") # Added transactions router
app.include_router(currencies.router, prefix="/api/v1/currencies") # Added currencies router
app.include_router(balances.router) # Added balances router
app.include_router(conversion_rates.router) # Added conversion_rates router
app.include_router(beta.router, prefix="/api/v1") # Added beta router


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Expense Tracker API!"}
