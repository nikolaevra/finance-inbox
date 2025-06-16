from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import requests

auth_scheme = HTTPBearer()

def get_current_user(request: Request, token=Depends(auth_scheme)):
    try:
        jwt = token.credentials
        user_info = requests.get(
            "https://api.clerk.dev/v1/me",
            headers={"Authorization": f"Bearer {jwt}"}
        ).json()
        return {
            "user_id": user_info["id"],
            "email": user_info["email_addresses"][0]["email_address"]
        }
    except:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")
