"""
Authentication Schemas - Request/Response Validation
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict  # type: ignore[import]

class RegisterRequest(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

class LoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    profile_picture: Optional[str]
    is_active: bool
    is_admin: bool
