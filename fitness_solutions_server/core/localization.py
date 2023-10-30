from babel import Locale, UnknownLocaleError
from fastapi import Header
from starlette_context import context, request_cycle_context
from starlette_context.plugins import Plugin

# from sqlalchemy_utils import TranslationHybrid
from .i18n import TranslationHybrid

DEFAULT_LOCALE = "en"


class AcceptLanguagePlugin(Plugin):
    key = "Accept-Language"


async def accept_language_dependency(
    accept_language: str | None = Header(None, example="en")
):
    data = {"accept_language": accept_language}
    with request_cycle_context(data):
        # yield allows it to pass along to the rest of the request
        yield


def get_locale():
    # TODO: Check if context exists (otherwise we might crash if accessed outside)
    locale = context.get("accept_language")

    if locale:
        locale = locale.split(",")[0]
    else:
        locale = DEFAULT_LOCALE

    return locale


class TranslationDict(dict[str, str]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            examples=[{"en": "Some title", "da_DK": "En titel"}],
            description="""A dictionary containing translations.
                Keys must be valid locales and values must be strings.
                You must always supply a value for at least one locale
            """,
        )

    @classmethod
    def validate(cls, v):
        if not isinstance(v, dict):
            raise TypeError("Dictionary required")
        try:
            for locale, value in v.items():
                if not isinstance(locale, str) or not isinstance(value, str):
                    raise TypeError("Dictionary must only contain strings")
                Locale.parse(locale, resolve_likely_subtags=False)
        except UnknownLocaleError:
            raise ValueError("Invalid locale")

        if len(v.keys()) == 0:
            raise ValueError("Must contain at least one locale")

        return cls(v)

    def __repr__(self):
        return f"TranslationDict({super().__repr__()})"


translation_hybrid = TranslationHybrid(
    current_locale=get_locale, default_locale=DEFAULT_LOCALE
)
