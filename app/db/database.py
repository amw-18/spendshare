from sqlmodel import SQLModel, create_engine

# For SQLite, the URL starts with sqlite:///
# For local development, we'll use a file-based SQLite database.
DATABASE_URL = "sqlite:///./test.db" 
# Later, this can be changed to your MySQL connection string, e.g.:
# MYSQL_USER = "your_user"
# MYSQL_PASSWORD = "your_password"
# MYSQL_SERVER = "your_server"
# MYSQL_DB = "your_db"
# DATABASE_URL = f"mysql+mysqlclient://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_SERVER}/{MYSQL_DB}"


# The connect_args is needed only for SQLite to allow multiple threads to access the same connection.
# This is relevant for FastAPI's background tasks or when running in a multithreaded server.
engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    # This function will create all tables in the database
    # based on the SQLModel models that have been defined.
    # It should be called once when the application starts.
    SQLModel.metadata.create_all(engine)

# It's also common to have a function to get a database session for dependency injection in FastAPI routes
# from sqlmodel import Session
# def get_session():
#     with Session(engine) as session:
#         yield session
# We will add this later when we implement the routers.
