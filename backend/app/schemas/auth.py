from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request"""
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None


class PasswordChange(BaseModel):
    """Password change request"""
    old_password: str
    new_password: str
