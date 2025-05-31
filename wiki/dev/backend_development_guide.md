# SpendShare: Backend Development Guide

This guide provides detailed instructions and best practices for backend development on the SpendShare project.

## 1. Environment Setup

*   **Python Version:** Ensure you have Python 3.10 or higher installed.
*   **Virtual Environment (uv):** We use `uv` for managing virtual environments and dependencies.
    *   Navigate to the project root: `cd /Users/awalsangikar/personal/spendshare/app`
    *   Create the virtual environment if it doesn't exist: `uv venv` (This will create a `.venv` directory).
    *   Activate the virtual environment:
        *   From backend project root (`/Users/awalsangikar/personal/spendshare/app`): `source .venv/bin/activate`
*   **Dependencies:**
    *   The backend dependencies are defined in `app/pyproject.toml`.
    *   To install or synchronize dependencies: `uv sync app/pyproject.toml` (after activating the venv, prefer `uv sync` if `pyproject.toml` is the primary source of truth for dependencies).

## 2. Core Principles

*   **API-First Design:** The `openapi.json` file (located in the project root) is the **single source of truth** for the API contract. All API changes must be reflected here.
*   **FastAPI Framework:** The backend is built using the FastAPI framework.

## 3. Development Workflow: Test-Driven Development (TDD)

We strictly follow a Test-Driven Development approach. **Write tests before you write implementation code.**

1.  **Understand Requirements & Design API Changes:**
    *   Clearly define the feature, its use cases, and how it impacts the existing system.
    *   Draft the necessary API endpoint changes (new endpoints, modifications to existing ones) in `openapi.json` first. This includes request/response schemas and paths.
    *   **Example:** If you're adding a new endpoint for creating expenses, add the path and necessary parameters in `openapi.json`.

2.  **Write Tests First (`./app/tests/`):
    *   **Structure:** Organize tests logically, typically in files corresponding to the API resource (e.g., `test_users.py`, `test_expenses.py`).
    *   **Tools:** Use `pytest` with `pytest-asyncio` for asynchronous code and `httpx.AsyncClient` for making API calls to your application during tests.
    *   **Coverage - Be Thorough!**
        *   **Happy Paths:** Test successful creation, retrieval, update, and deletion of resources.
        *   **Edge Cases:** Consider empty inputs, maximum/minimum values, unusual but valid inputs.
        *   **Error Conditions:** Test how the API responds to invalid data (e.g., incorrect types, missing required fields - expect `422 Unprocessable Entity`), non-existent resources (expect `404 Not Found`), etc.
        *   **Authorization & Authentication:**
            *   Ensure endpoints requiring authentication return `401 Unauthorized` if no token or an invalid token is provided.
            *   Verify that users can only access/modify resources they are permitted to (expect `403 Forbidden` or `404 Not Found` as appropriate).
        *   **Integration Points:** For a new feature, consider its interaction with existing features and write tests that cover these integrations.
    *   **Fixtures (`conftest.py` and local test file fixtures):
        *   Use fixtures extensively to set up prerequisite data (e.g., create test users, groups, currencies) and provide authenticated API clients.
        *   Example: `normal_user_token_headers`, `admin_user_token_headers`, `test_currency_sync` (as seen in `test_expenses.py`).
    *   **Assertions:**
        *   Assert HTTP status codes rigorously (e.g., `assert response.status_code == status.HTTP_201_CREATED`).
        *   Assert the content of the response body, including specific field values and the presence/absence of certain keys.
    *   **Example Test Structure (Conceptual from `test_expenses.py`):
        ```python
        import pytest
        from httpx import AsyncClient
        from fastapi import status

        @pytest.mark.asyncio
        async def test_new_feature_creation(client: AsyncClient, normal_user_token_headers: dict, test_currency: Currency):
            payload = {
                "name": "Test Feature Item",
                "value": 100,
                "currency_id": test_currency.id
            }
            response = await client.post("/api/v1/new-feature/", json=payload, headers=normal_user_token_headers)
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["name"] == payload["name"]
            # ... more assertions

        @pytest.mark.asyncio
        async def test_new_feature_unauthorized(client: AsyncClient):
            response = await client.get("/api/v1/new-feature/some_id")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        ```

3.  **Implement API Endpoints & Business Logic:**
    *   Write the FastAPI path operation functions in the appropriate router files (e.g., in `src/routers/`).
    *   Implement the business logic in the routers themselves.
    *   Define Pydantic models for request and response bodies in `src/models/schemas.py` (or similar) if not already covered by `openapi.json` generation, ensuring they align with the spec.

4.  **Run Tests & Iterate:**
    *   Continuously run your tests as you develop: `pytest` (or `uv run pytest`).
    *   Refactor your code and fix bugs until all tests pass.
    *   Use `pytest --ff` to run failing tests first and optionally add the `-x` flag as well to only test the failing tests.

5.  **Update/Verify `openapi.json`:**
    *   After your implementation is complete and tests pass, ensure `openapi.json` accurately reflects all changes. If your project uses a tool to generate `openapi.json` from code, run it. Otherwise, update it manually with extreme care.
    *   **This step is critical for frontend and other API consumers.**

## 4. Python Best Practices

*   **Clean Code:** Write readable, maintainable, and self-documenting code.
*   **Type Hinting:** Use Python type hints for all function signatures and variables. This is crucial for FastAPI and Pydantic.
*   **Modularity:** Break down complex logic into smaller, reusable functions and classes.
*   **Error Handling:** Implement robust error handling. Use FastAPI's exception handling mechanisms where appropriate.
*   **Logging:** Add meaningful logging for debugging and monitoring (`loguru` python module, install of not present in `pyproject.toml`).
*   **Security:** Be mindful of security best practices (e.g., input validation, protection against common web vulnerabilities, secure handling of sensitive data).
*   **Database Interactions:** Use SQLAlchemy Core or ORM correctly. Be mindful of query performance and potential race conditions.

## 6. Future Development Focus: Expense Settlement

The primary roadmap item is the implementation of the **Expense Settlement** feature. This will involve:
*   New API endpoints for managing user crypto preferences (prioritized list, wallet addresses).
*   Endpoints for initiating, tracking, and confirming settlements.
*   Complex business logic for multi-currency settlements using latest exchange rates.
*   Refer to the "Future Development & Roadmap" section in the previous top-level developer guide (now archived or to be merged here) for detailed anticipated API changes and considerations.

This will require careful TDD, robust error handling, and precise `openapi.json` updates.
If possible, confirm the correct `openapi.json` by generating it from the fastapi app after implementation and commit the changes as part of
the implementation.
