# TODO: Remove this once PR is merged for fix (https://github.com/kvesteri/sqlalchemy-utils/pull/705)

import sqlalchemy as sa
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import MappedColumn
from sqlalchemy.sql.expression import ColumnElement

try:
    import babel
    import babel.dates
except ImportError:
    babel = None  # type: ignore


def get_locale():
    try:
        return babel.Locale("en")
    except AttributeError:
        # As babel is optional, we may raise an AttributeError accessing it
        raise Exception()


def cast_locale(obj, locale, attr):
    """
    Cast given locale to string. Supports also callbacks that return locales.

    :param obj:
        Object or class to use as a possible parameter to locale callable
    :param locale:
        Locale object or string or callable that returns a locale.
    """
    if callable(locale):
        try:
            locale = locale(obj, get_key(attr))
        except TypeError:
            try:
                locale = locale(obj)
            except TypeError:
                locale = locale()
    if isinstance(locale, babel.Locale):
        return str(locale)
    return locale


class cast_locale_expr(ColumnElement):
    inherit_cache = False

    def __init__(self, cls, locale, attr):
        self.cls = cls
        self.locale = locale
        self.attr = attr


@compiles(cast_locale_expr)
def compile_cast_locale_expr(element, compiler, **kw):
    locale = cast_locale(element.cls, element.locale, element.attr)
    if isinstance(locale, str):
        return f"'{locale}'"
    return compiler.process(locale)


def get_key(attr):
    if isinstance(attr, MappedColumn):
        return attr.column.key
    else:
        return attr.key


class TranslationHybrid:
    def __init__(self, current_locale, default_locale, default_value=None):
        self.current_locale = current_locale
        self.default_locale = default_locale
        self.default_value = default_value

    def getter_factory(self, attr):
        """
        Return a hybrid_property getter function for given attribute. The
        returned getter first checks if object has translation for current
        locale. If not it returns the first available translation. If there
        is no translation found it returns None.
        """

        def getter(obj):
            current_locale = cast_locale(obj, self.current_locale, attr)
            try:
                return getattr(obj, get_key(attr))[current_locale]
            except (TypeError, KeyError):
                try:
                    return next(iter(getattr(obj, get_key(attr)).items()))[1]
                except (TypeError, KeyError, StopIteration):
                    return self.default_value

        return getter

    def setter_factory(self, attr):
        def setter(obj, value):
            if getattr(obj, get_key(attr)) is None:
                setattr(obj, get_key(attr), {})
            locale = cast_locale(obj, self.current_locale, attr)
            getattr(obj, get_key(attr))[locale] = value

        return setter

    def expr_factory(self, attr):
        def expr(cls):
            cls_attr = getattr(cls, get_key(attr))
            current_locale = cast_locale_expr(cls, self.current_locale, attr)
            return sa.func.coalesce(
                cls_attr[current_locale].astext,
                sa.func.jsonb_path_query_array(
                    cls_attr, sa.literal("$.*", literal_execute=True)
                ).op("->>")(sa.literal(0, literal_execute=True)),
            )

        return expr

    def __call__(self, attr):
        return hybrid_property(
            fget=self.getter_factory(attr),
            fset=self.setter_factory(attr),
            expr=self.expr_factory(attr),
        )
