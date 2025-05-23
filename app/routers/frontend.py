from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional # Add Optional for type hinting

from app.db.database import get_session
from app.models import schemas, models # Ensure models is imported for type hints if needed by CRUD
from app.crud import crud_user, crud_group
# from app.core.security import get_password_hash # Not using directly now

router = APIRouter(
    tags=["frontend"],
    default_response_class=HTMLResponse # Default to HTML responses for this router
)

@router.get("/", name="get_home_page", include_in_schema=False)
async def get_home_page(request: Request):
    user_id = request.cookies.get("fake_session_user_id")
    if user_id: # If "logged in", go to dashboard
        return RedirectResponse(url=request.url_for("get_dashboard_page"), status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=request.url_for("get_login_page"), status_code=status.HTTP_302_FOUND) # Else, go to login

@router.get("/signup", name="get_signup_page", include_in_schema=False)
async def get_signup_page(request: Request, error: Optional[str] = None):
    return request.app.state.templates.TemplateResponse("signup.html", {"request": request, "error": error})

@router.post("/signup", name="handle_signup", include_in_schema=False)
async def handle_signup(
    request: Request,
    session: AsyncSession = Depends(get_session),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    user_in = schemas.UserCreate(username=username, email=email, password=password)
    db_user_by_email = await crud_user.get_user_by_email(session, email=user_in.email)
    if db_user_by_email:
        return RedirectResponse(url=request.url_for("get_signup_page") + "?error=Email+already+exists", status_code=status.HTTP_303_SEE_OTHER)
    db_user_by_username = await crud_user.get_user_by_username(session, username=user_in.username)
    if db_user_by_username:
        return RedirectResponse(url=request.url_for("get_signup_page") + "?error=Username+already+exists", status_code=status.HTTP_303_SEE_OTHER)
    
    await crud_user.create_user(session=session, user_in=user_in)
    return RedirectResponse(url=request.url_for("get_login_page") + "?message=Signup+successful,+please+login.", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login", name="get_login_page", include_in_schema=False)
async def get_login_page(request: Request, message: Optional[str] = None, error: Optional[str] = None):
    return request.app.state.templates.TemplateResponse("login.html", {"request": request, "message": message, "error": error})

@router.post("/login", name="handle_login", include_in_schema=False)
async def handle_login(
    request: Request,
    session: AsyncSession = Depends(get_session),
    username: str = Form(...), 
    password: str = Form(...)
):
    user = await crud_user.get_user_by_username(session, username=username)
    if not user:
        user = await crud_user.get_user_by_email(session, email=username)
    
    if not user or not crud_user.verify_password(password, user.hashed_password): # Use the actual password verification
        return RedirectResponse(url=request.url_for("get_login_page") + "?error=Invalid+username+or+password", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url=request.url_for("get_dashboard_page"), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="fake_session_user_id", value=str(user.id), httponly=True, samesite="Lax", max_age=3600) # Max age 1 hour
    return response
    
@router.get("/logout", name="handle_logout", include_in_schema=False)
async def handle_logout(request: Request):
    response = RedirectResponse(url=request.url_for("get_login_page") + "?message=Logged+out+successfully.", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="fake_session_user_id", httponly=True, samesite="Lax")
    return response

@router.get("/dashboard", name="get_dashboard_page", include_in_schema=False)
async def get_dashboard_page(request: Request, session: AsyncSession = Depends(get_session)):
    user_id_str = request.cookies.get("fake_session_user_id")
    current_user: Optional[models.User] = None
    if user_id_str:
        try:
            current_user = await crud_user.get_user(session, user_id=int(user_id_str))
        except ValueError: # Handle cases where cookie value is not a valid int
            pass 
    
    if not current_user:
        return RedirectResponse(url=request.url_for('get_login_page') + "?error=Please+login+to+view+the+dashboard.", status_code=status.HTTP_302_FOUND)

    all_other_users = await crud_user.get_users(session=session, skip=0, limit=1000) # Fetch users for "add friends" simulation
    # Filter out the current user from the list of "all_other_users"
    all_other_users = [user for user in all_other_users if user.id != current_user.id]

    # For groups, let's display groups the user is a member of, or has created.
    # This requires a more complex query or multiple queries.
    # For now, using get_groups_for_user (creator) and then manually adding groups they are a member of.
    created_groups = await crud_group.get_groups_created_by_user(session=session, user_id=current_user.id)
    member_of_groups = await crud_group.get_groups_for_member(session=session, user_id=current_user.id)
    
    # Combine and deduplicate groups
    user_groups_dict = {group.id: group for group in created_groups}
    for group in member_of_groups:
        user_groups_dict[group.id] = group
    user_groups = list(user_groups_dict.values())

    return request.app.state.templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "users": all_other_users,
        "groups": user_groups
    })

@router.post("/create-group", name="handle_create_group", include_in_schema=False)
async def handle_create_group(
    request: Request,
    session: AsyncSession = Depends(get_session),
    group_name: str = Form(...),
    group_description: Optional[str] = Form(None)
):
    user_id_str = request.cookies.get("fake_session_user_id")
    if not user_id_str:
        return RedirectResponse(url=request.url_for('get_login_page') + "?error=Please+login+to+create+groups.", status_code=status.HTTP_302_FOUND)
    
    current_user_id = int(user_id_str)
    group_in = schemas.GroupCreate(name=group_name, description=group_description, created_by_user_id=current_user_id)
    await crud_group.create_group(session=session, group_in=group_in) # create_group already adds creator as member
    return RedirectResponse(url=request.url_for("get_dashboard_page") + "?message=Group+created+successfully", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/groups/{group_id}", name="get_group_page", include_in_schema=False)
async def get_group_page(request: Request, group_id: int, session: AsyncSession = Depends(get_session), error: Optional[str] = None, message: Optional[str] = None):
    user_id_str = request.cookies.get("fake_session_user_id")
    current_user: Optional[models.User] = None
    if user_id_str:
        current_user = await crud_user.get_user(session, user_id=int(user_id_str))
    
    if not current_user:
        return RedirectResponse(url=request.url_for('get_login_page') + "?error=Please+login+to+view+groups.", status_code=status.HTTP_302_FOUND)

    group = await crud_group.get_group_with_members(session=session, group_id=group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Users available to be added to the group (e.g., all users not already in the group)
    all_users = await crud_user.get_users(session=session, limit=1000)
    group_member_ids = {member.id for member in group.members}
    users_to_add = [user for user in all_users if user.id not in group_member_ids]

    return request.app.state.templates.TemplateResponse("view_group.html", {
        "request": request,
        "group": group,
        "user": current_user,
        "users_to_add": users_to_add, # Pass users that can be added
        "error": error,
        "message": message
    })

@router.post("/groups/{group_id}/add-member", name="handle_add_member_to_group", include_in_schema=False)
async def handle_add_member_to_group(
    request: Request,
    group_id: int,
    user_id_to_add: int = Form(..., alias="user_id"), # Alias from form field name
    session: AsyncSession = Depends(get_session)
):
    requesting_user_id_str = request.cookies.get("fake_session_user_id")
    if not requesting_user_id_str:
        return RedirectResponse(url=request.url_for('get_login_page') + "?error=Please+login", status_code=status.HTTP_302_FOUND)
    
    # Permission check: For now, allow any logged-in user to add.
    # A real app would check if requesting_user_id has rights for this group.
    
    try:
        updated_group = await crud_group.add_member_to_group(session=session, group_id=group_id, user_id=user_id_to_add)
        if updated_group is None: # Should not happen if crud raises exceptions for not found
             return RedirectResponse(url=request.url_for("get_group_page", group_id=group_id) + "?error=Failed+to+add+member.+Group+or+user+not+found.", status_code=status.HTTP_303_SEE_OTHER)
        return RedirectResponse(url=request.url_for("get_group_page", group_id=group_id) + "?message=Member+added+successfully.", status_code=status.HTTP_303_SEE_OTHER)
    except HTTPException as e:
        return RedirectResponse(url=request.url_for("get_group_page", group_id=group_id) + f"?error={e.detail.replace(' ', '+')}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e: # Catch any other unexpected errors
        return RedirectResponse(url=request.url_for("get_group_page", group_id=group_id) + f"?error=An+unexpected+error+occurred.", status_code=status.HTTP_303_SEE_OTHER)
