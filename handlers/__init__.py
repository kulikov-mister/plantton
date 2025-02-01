#
from aiogram import Router
from typing import List
from . import default, admin, payments, donate, empty, plants, test


routers: List[Router] = [
    default.router,
    admin.router,
    payments.router,
    plants.router,
    donate.router,
    empty.router,
    test.router,
]


router: Router = Router(name="admin_main")
router.include_routers(*routers)


__all__ = "router"
