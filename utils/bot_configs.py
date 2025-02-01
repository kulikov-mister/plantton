from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault
from lang.translator import LANG_CODE_LIST, LocalizedTranslator, Translator
from config import is_tech_works


async def set_bot_configs(bot: Bot, locale: str):
    await set_commands(bot, locale)
    if not is_tech_works:
        await set_bot_name(bot, locale)  # TODO: Flood control
        await set_bot_description(bot, locale)


async def set_commands(bot: Bot, locale: str):
    translator: LocalizedTranslator = Translator().get_translator(locale)
    commands = [
        BotCommand(
            command='start',
            description=translator.get("start_cmd_description")
        ),
        BotCommand(
            command='plants',
            description=translator.get("plants_cmd_description")
        ),
        BotCommand(
            command='balance',
            description=translator.get("balance_cmd_description")
        ),
        BotCommand(
            command='pro',
            description=translator.get("pro_cmd_description")
        ),
        BotCommand(
            command='help',
            description=translator.get("help_cmd_description")
        ),
        BotCommand(
            command='privacy',
            description=translator.get("privacy_cmd_description")
        ),
        BotCommand(
            command='terms',
            description=translator.get("terms_cmd_description")
        ),
        BotCommand(
            command='close',
            description=translator.get("close_cmd_description")
        )
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def set_bot_description(bot: Bot, locale: str) -> None:
    translator: LocalizedTranslator = Translator().get_translator(locale)
    await bot.set_my_short_description(
        short_description=translator.get("bot_short_description"), language_code=locale
    )
    await bot.set_my_description(
        description=translator.get("bot_description"), language_code=locale
    )


async def set_bot_name(bot: Bot, locale: str) -> None:
    translator: LocalizedTranslator = Translator().get_translator(locale)
    await bot.set_my_name(
        name=translator.get("bot_name"), language_code=locale
    )
