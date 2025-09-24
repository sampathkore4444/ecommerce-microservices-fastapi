from fastapi import HTTPException, Header
import httpx
import os

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")

        # Verify token with user service
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")

            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="User service unavailable")
