import json
from pyramid.i18n import TranslationString as TS
from pyramid.i18n import get_localizer
from translationstring.compat import text_type
from eduid_am.user import User

translation_domain = 'eduid-dashboard'


class JSONAwareTranslationStringProxy(object):

    def __init__(self, s, **kwargs):
        self._ts = TS(s, **kwargs)

    def __getattr__(self, name):
        try:
            return getattr(self._ts, name)
        except AttributeError:
            return super(JSONAwareTranslationStringProxy, self).__getattr__(name)

    def __getstate__(self):
        return self._ts.__dict__

    def __unicode__(self):
        return unicode(self._ts)

    def __str__(self):
        return str(self._ts)

    def __json__(self, request):
        return get_localizer(request).translate(self._ts)


def TranslationStringFactory(domain):
    def create(msgid, mapping=None, default=None):
        if not isinstance(msgid, basestring):
            return msgid
        return JSONAwareTranslationStringProxy(msgid, domain=translation_domain,
                mapping=mapping, default=default)
    return create

TranslationString = TranslationStringFactory(translation_domain)


class I18NJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, JSONAwareTranslationStringProxy):
            raise TypeError()
        return json.JSONEncoder.default(self, obj)


def I18NJSONEncoderFactory(request):
    class I18NAwareJSONEncoder(json.JSONEncoder):

        def __init__(self, *args, **kwargs):
            super(I18NAwareJSONEncoder, self).__init__(*args, **kwargs)
            self.request = request

        def default(self, obj):
            if isinstance(obj, JSONAwareTranslationStringProxy):
                return get_localizer(self.request).translate(obj._ts)
            return json.JSONEncoder.default(self, obj)


    return I18NAwareJSONEncoder


def i18n_json_adapter(obj, request):
    return get_localizer(request).translate(obj)


def locale_negotiator(request):
    settings = request.registry.settings
    available_languages = settings['available_languages'].keys()
    cookie_name = settings['lang_cookie_name']

    cookie_lang = request.cookies.get(cookie_name, None)
    if cookie_lang and cookie_lang in available_languages:
        return cookie_lang

    user = request.session.get('user')
    if user:
        preferredLanguage = user.get_preferred_language()
        if preferredLanguage:
            return preferredLanguage

    return request.accept_language.best_match(available_languages)
