#
from aiogram import Router
from typing import List
from . import admin, payments, donate, default, test, empty


routers: List[Router] = [
    admin.router,
    payments.router,
    donate.router,
    default.router,
    test.router,
    empty.router
]


router: Router = Router(name="admin_main")
router.include_routers(*routers)


__all__ = "router"
