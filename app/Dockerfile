# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR .

# Install uv (Python package installer)
# Ensure pip is up-to-date and install uv
RUN python -m pip install --upgrade pip && \
    pip install uv

# Copy the dependency files
# pyproject.toml and uv.lock are in the same directory as the Dockerfile (app/)
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv
# This command assumes your virtual environment is managed by uv and dependencies are synced.
RUN uv sync

# Copy the application source code
# src/ is a subdirectory of the current build context (app/)
COPY src/ ./src/

# Copy the .env file into the container
# This file should be created by the user from .env.example and contain production settings.
COPY .env ./

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn via uv run
# Ensure it listens on all interfaces (0.0.0.0) and the correct port (8000)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
