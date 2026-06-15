"""
Modelos de base de datos SQLite.

Proporciona acceso a todas las tablas:
- users (usuarios y operadores)
- devices
- bandwidth_profiles
- sessions
- traffic_snapshots
- dns_categories y dns_entries
- audit_log
- router_sync_log
"""

from .database import Database, init_db, get_db, close_db
from .user import UserModel, OperatorModel
from .device import DeviceModel
from .profile import ProfileModel
from .session import SessionModel
from .traffic import TrafficModel
from .dns_entry import DNSCategoryModel, DNSEntryModel
from .audit_log import AuditLogModel
from .router_sync import RouterSyncLogModel

__all__ = [
    "Database",
    "init_db",
    "get_db",
    "close_db",
    "UserModel",
    "OperatorModel",
    "DeviceModel",
    "ProfileModel",
    "SessionModel",
    "TrafficModel",
    "DNSCategoryModel",
    "DNSEntryModel",
    "AuditLogModel",
    "RouterSyncLogModel",
]
