#
from aiogram import Router
from typing import List
from . import default, admin, payments, books, donate, empty, test


routers: List[Router] = [
    default.router,
    admin.router,
    payments.router,
    books.router,
    donate.router,
    empty.router,
    test.router,
]


router: Router = Router(name="admin_main")
router.include_routers(*routers)


__all__ = "router"
