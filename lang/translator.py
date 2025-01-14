from typing import Dict, List, Optional, Tuple
from fluent_compiler.bundle import FluentBundle
from fluentogram import TranslatorHub, FluentTranslator, TranslatorRunner


FLUENT_DICTIONARIES_PATH_DICT: Dict[str, str] = {
    "en": "lang/locales/en.ftl",
    "ru": "lang/locales/ru.ftl",
}

FLUENT_TRANSLATORS: List[FluentTranslator] = [
    FluentTranslator(
        locale=locale,
        translator=FluentBundle.from_files(
            locale=locale, filenames=[FLUENT_DICTIONARIES_PATH_DICT[locale]]
        ),
    )
    for locale in FLUENT_DICTIONARIES_PATH_DICT
]

FLUENT_LOCALES_MAP: Dict[str, Tuple[str]] = {
    "en": ("en",),  # English
    "ru": ("ru", "en"),  # Russian
}

LOCALS_BY_NAME: Dict[str, str] = {
    "Русский 🇷🇺": "ru",
    "English 🇺🇸": "en",
}

LOCALS_BY_CODE: Dict[str, str] = {LOCALS_BY_NAME[i]: i for i in LOCALS_BY_NAME}
LANG_CODE_LIST: List[str] = list(LOCALS_BY_NAME.values())

ROOT_LOCALE: str = "ru"


class LocalizedTranslator:
    """
    The `LocalizedTranslator` class is a wrapper around a `TranslatorRunner` object that provides
    localized translations based on a specified locale.
    """

    translator: TranslatorRunner
    locale: str
    __translator_cache: Dict[str, Dict[str, str]] = {
        locale: {} for locale in LANG_CODE_LIST
    }

    def __init__(self, translator: TranslatorRunner, locale: str):
        """
        The function initializes an object with a translator and a locale.

        :param translator: The `translator` parameter is an instance of the `TranslatorRunner` class. It is
        used to perform translation operations
        :type translator: TranslatorRunner
        :param locale: The `locale` parameter is a string that represents the specific language and region
        for which the translation is being performed. It is used to determine the appropriate translation
        rules and language-specific formatting. Examples of locale strings include "en_US" for English
        (United States) and "fr_FR" for French (
        :type locale: str
        """
        self.translator = translator
        self.locale = locale

    def get(self, key: str, **kwargs) -> str:
        """
        The `get` function retrieves a translation for a given key, either from a cache or from a
        translator, and returns the translation or the key itself if no translation is found.

        :param key: The `key` parameter is a string that represents the translation key. It is used to look
        up the translation for a specific text or phrase
        :type key: str
        :return: a string.
        """
        data: Optional[str] = None

        if not kwargs:
            data = LocalizedTranslator.__translator_cache[self.locale].get(key)

        if not data:
            data: str = self.translator.get(key, **kwargs)
            LocalizedTranslator.__translator_cache[self.locale][key] = data

        if not data:
            # bot_logger.error(f"There's no any translation for key {key}")
            print(f"There's no any translation for key {key}")
            data = str(key)

        return data


class Translator:
    """
    The `Translator` class is a singleton that initializes a `TranslatorHub` object and provides access
    to localized translators based on the specified locale.
    """

    t_hub: TranslatorHub
    translators: Dict[str, LocalizedTranslator] = {}

    def __new__(cls):
        """
        The above function is a singleton implementation that ensures only one instance of the Translator
        class is created.

        :param cls: cls is the class object itself. In this case, it refers to the class "Translator"
        :return: The `__new__` method is returning the instance of the `Translator` class.
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(Translator, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        """
        The function initializes a TranslatorHub object with specified locales, translators, and root
        locale.
        """
        self.t_hub = TranslatorHub(
            locales_map=FLUENT_LOCALES_MAP,
            translators=FLUENT_TRANSLATORS,
            root_locale=ROOT_LOCALE,
        )
        self.__init_translators()

    def __init_translators(self) -> None:
        """
        The function initializes translators for each locale using the t_hub object.
        """
        for locale in self.t_hub.locales_map:
            self.translators[locale] = LocalizedTranslator(
                translator=self.t_hub.get_translator_by_locale(locale), locale=locale
            )

    def get_translator(self, locale: str) -> LocalizedTranslator:
        """
        The function `get_translator` returns a `LocalizedTranslator` object based on the specified locale,
        or the root locale if the specified locale is not found.

        :param locale: The `locale` parameter is a string that represents the language and region for which
        a translator is needed
        :type locale: str
        :return: The method is returning an instance of the `LocalizedTranslator` class.
        """
        if locale not in self.translators:
            locale = self.t_hub.root_locale

        return self.translators[locale]
