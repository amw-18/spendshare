# Environment Setup with uv

This project uses `uv` for Python environment and package management.

## Prerequisites

Ensure you have `uv` installed. If not, you can install it following the official instructions (e.g., `pip install uv`, or from astral.sh).

## Setup Steps

1.  **Create a Virtual Environment:**
    Open your terminal in the project root directory and run:
    ```bash
    uv venv
    ```
    This will create a virtual environment named `.venv` in the project root.

2.  **Activate the Virtual Environment:**
    *   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows (PowerShell):
        ```bash
        .venv\Scripts\Activate.ps1
        ```
    *   On Windows (CMD):
        ```bash
        .venv\Scripts\activate.bat
        ```

3.  **Install Dependencies:**
    Once the virtual environment is activated, install the required packages from `requirements.txt`:
    ```bash
    uv pip install -r requirements.txt
    ```

## Running the Application

(Instructions for running the application will be added here later, e.g., using `uvicorn app.main:app --reload`)

## Running Tests

(Instructions for running tests with `pytest` will be added here later)
