"""
schemas.py — Esquemas Pydantic para validación de datos
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== USERS ==========
class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    cedula: str = Field(..., min_length=5, max_length=20)
    cargo: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    asset_tag: Optional[str] = None
    device_type: str = Field(default="PC")
    mac_address: str = Field(..., regex=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    profile: str = Field(default="ESTANDAR")
    expires_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    profile: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    cedula: str
    cargo: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    asset_tag: Optional[str]
    device_type: str
    mac_address: str
    ip_address: Optional[str]
    profile: str
    status: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== DEVICES ==========
class DeviceCreate(BaseModel):
    user_id: int
    mac_address: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    mac_address: str
    device_name: Optional[str]
    device_type: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========== OPERATORS ==========
class OperatorCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = Field(default="SOPORTE")


class OperatorUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    enabled: Optional[bool] = None


class OperatorResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ========== AUTH ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ========== DNS ==========
class DNSCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool

    class Config:
        from_attributes = True


class DNSEntryCreate(BaseModel):
    category_id: int
    domain: str


class DNSEntryResponse(BaseModel):
    id: int
    category_id: int
    domain: str
    enabled: bool

    class Config:
        from_attributes = True


# ========== QoS ==========
class BandwidthProfileResponse(BaseModel):
    id: int
    name: str
    max_limit_down: str
    max_limit_up: str
    priority: int
    enabled: bool

    class Config:
        from_attributes = True


# ========== STATISTICS ==========
class UserStatsResponse(BaseModel):
    user_id: int
    mac_address: str
    is_online: bool
    current_ip: Optional[str]
    bytes_in: int
    bytes_out: int
    session_duration: Optional[int]


class DashboardStatsResponse(BaseModel):
    total_users: int
    active_users: int
    top_consumers: List[UserStatsResponse]
    expiring_soon: List[UserResponse]
    total_bandwidth_24h: int


# ========== SESSIONS ==========
class SessionResponse(BaseModel):
    id: int
    user_id: int
    mac_address: str
    ip_address: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    bytes_in: int
    bytes_out: int

    class Config:
        from_attributes = True


# ========== AUDIT ==========
class AuditLogResponse(BaseModel):
    id: int
    operator_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    status: str
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True
