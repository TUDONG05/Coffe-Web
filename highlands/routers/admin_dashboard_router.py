"""
Admin dashboard endpoints - commented out to use simple list endpoints instead.
Dashboard data is calculated from individual admin API endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin-dashboard"])


# Note: Dashboard functionality is provided by querying:
# - /api/admin/orders for order statistics
# - /api/admin/customers for customer count
# - /api/admin/products for product count
# These endpoints are already working and provide all dashboard data
