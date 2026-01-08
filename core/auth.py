from fastapi import HTTPException,Header,status
import os

AUTH_KEY = os.getenv("AUTH_KEY")

def static_auth(check_auth_key : str = Header(...,alias="CHECK_AUTH_KEY")):
    if not AUTH_KEY:
        raise HTTPException (status_code=status.HTTP_403_FORBIDDEN)
    if check_auth_key != AUTH_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
