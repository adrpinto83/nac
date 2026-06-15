"""
routers package — API endpoints
"""

from . import auth, users, devices, operators, stats, dns, qos

__all__ = ["auth", "users", "devices", "operators", "stats", "dns", "qos"]
