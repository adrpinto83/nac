"""Esquemas Pydantic para validación de requests/responses."""

from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    StatusResponse,
    HealthCheckResponse,
)
from .user import UserCreate, UserUpdate, UserResponse, OperatorCreate, OperatorResponse, LoginRequest, TokenResponse
from .device import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceWithUserResponse, ARPDevice, LiveDevicesResponse
from .dashboard import DashboardMetrics, TopDevicesByTraffic, Alert, UnregisteredMAC, DeviceStats
from .profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    DNSCategoryCreate,
    DNSCategoryResponse,
    DNSEntryCreate,
    DNSEntryResponse,
)

__all__ = [
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "StatusResponse",
    "HealthCheckResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "OperatorCreate",
    "OperatorResponse",
    "LoginRequest",
    "TokenResponse",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceResponse",
    "DeviceWithUserResponse",
    "ARPDevice",
    "LiveDevicesResponse",
    "DashboardMetrics",
    "TopDevicesByTraffic",
    "Alert",
    "UnregisteredMAC",
    "DeviceStats",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "DNSCategoryCreate",
    "DNSCategoryResponse",
    "DNSEntryCreate",
    "DNSEntryResponse",
]
