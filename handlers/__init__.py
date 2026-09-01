from aiogram import Router
from .start import router as start_router
from .register import router as register_router
from .post_ad import router as post_ad_router
from .view_ads import router as view_ads_router
from .my_ads import router as my_ads_router
from .vip import router as vip_router
from .contact import router as contact_router
from .admin import router as admin_router

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(register_router)
    main_router.include_router(post_ad_router)
    main_router.include_router(view_ads_router)
    main_router.include_router(my_ads_router)
    main_router.include_router(vip_router)
    main_router.include_router(contact_router)
    main_router.include_router(admin_router)
    return main_router
