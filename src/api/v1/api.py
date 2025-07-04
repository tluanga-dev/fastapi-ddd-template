from fastapi import APIRouter

from src.api.v1.endpoints.auth import router as auth_router
from src.api.v1.endpoints.users import router as users_router
from src.api.v1.endpoints.roles import router as roles_router
from src.api.v1.endpoints.permissions import router as permissions_router
from src.api.v1.endpoints.locations import router as locations_router
from src.api.v1.endpoints.categories import router as categories_router
from src.api.v1.endpoints.brand_endpoints import router as brands_router
from src.api.v1.endpoints.customer_endpoints import router as customers_router
from src.api.v1.endpoints.customer_analytics import router as customer_analytics_router
from src.api.v1.endpoints.supplier_endpoints import router as suppliers_router
from src.api.v1.endpoints.supplier_analytics import router as supplier_analytics_router
from src.api.v1.endpoints.item_master_endpoints import router as item_masters_router
from src.api.v1.endpoints.sku_endpoints import router as skus_router
from src.api.v1.endpoints.inventory import router as inventory_router
from src.api.v1.endpoints.transaction import router as transaction_router
from src.api.v1.endpoints.rental_return import router as rental_return_router
from src.api.v1.endpoints.rental_transaction import router as rental_transaction_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(roles_router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
api_router.include_router(locations_router, prefix="/locations", tags=["locations"])
api_router.include_router(categories_router, prefix="/categories", tags=["categories"])
api_router.include_router(brands_router, prefix="/brands", tags=["brands"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
api_router.include_router(customer_analytics_router, tags=["customer-analytics"])
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(supplier_analytics_router, tags=["supplier-analytics"])
api_router.include_router(item_masters_router, prefix="/item-masters", tags=["item-masters"])
api_router.include_router(skus_router, prefix="/skus", tags=["skus"])
api_router.include_router(inventory_router, tags=["inventory"])
api_router.include_router(transaction_router, tags=["transactions"])
api_router.include_router(rental_return_router, tags=["rental-returns"])
api_router.include_router(rental_transaction_router, tags=["rental-transactions"])