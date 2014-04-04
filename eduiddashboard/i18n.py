import json
from pyramid.i18n import TranslationString as TS
from pyramid.i18n import get_localizer
from translationstring.compat import text_type
from eduid_am.user import User

translation_domain = 'eduid-dashboard'


class JSONAwareTranslationStringProxy(object):
    '''
    The reason for this proxy is to avoid automatic
    encoding of string types
    (translationstring.TranslationString *is* a string type)
    by Python's json module.
    There is no way of overriding the default encoding of
    json serializable objects in Python's json package.

    We want to do the translation when json encoding the
    translation string.
    '''

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
        '''
        This is to be used in the default json renderer
        of pyramid's rendering machinery, that kicks in when a view is
        decorated to be rendered as json and returns a ``dict`` (such as
        the eduiddashboard.views.userstatus:userstatus view).
        It is set up in the ``main`` function in eduiddashboard/__init__.py
        (line 446).

        The default JSON renderer in pyramid will call the __json__ method
        of an object if a TypeError is raised when it tries to encode it,
        and gives the request as a parameter to this method.
        '''
        return get_localizer(request).translate(self._ts)


def TranslationStringFactory(domain):
    '''
    This is simply to have the translation domain
    in the ``create`` closure. The code is 
    almost straight out of translationstring/__init__.py.
    The only difference (the ``if`` in ``create``)
    is to avoid nesting of proxies.
    '''
    def create(msgid, mapping=None, default=None):
        if not isinstance(msgid, basestring):
            return msgid
        return JSONAwareTranslationStringProxy(msgid, domain=translation_domain,
                mapping=mapping, default=default)
    return create

TranslationString = TranslationStringFactory(translation_domain)


def I18NJSONEncoderFactory(request):
    '''
    This is a closure around the request, to produce a json
    encoder (for Python's json standard module) that has
    the request and can translate translation strings at
    json encoding time.

    It is used when the json encoding (dumps) is explicitly done
    in the view, where we have the request (for example, in
    eduiddashboard/views/__init__.py line 117)
    '''
    class I18NAwareJSONEncoder(json.JSONEncoder):

        def __init__(self, *args, **kwargs):
            super(I18NAwareJSONEncoder, self).__init__(*args, **kwargs)
            self.request = request

        def default(self, obj):
            if isinstance(obj, JSONAwareTranslationStringProxy):
                return get_localizer(self.request).translate(obj._ts)
            return json.JSONEncoder.default(self, obj)


    return I18NAwareJSONEncoder


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
