from pyramid.i18n import get_locale_name
from pyramid.httpexceptions import HTTPFound, HTTPBadRequest
from pyramid.renderers import render_to_response
from pyramid.security import remember
from pyramid.view import view_config

from deform import Form, ValidationFailure

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.models import Person
from eduiddashboard.utils import verify_auth_token, get_am, flash


@view_config(route_name='home', renderer='templates/home.jinja2')
def home(context, request):
    user = request.session.get('user', None)
    schema = Person()
    form = Form(schema, buttons=('submit',))
    if request.POST:
        controls = request.POST.items()
        try:
            user_modified = form.validate(controls)
        except ValidationFailure:
            flash(request, 'error',
                  _('Please fix the highlighted errors in the form'))
            person = schema.serialize(user)
        else:
            person = schema.serialize(user_modified)
            # Do the save staff
            flash(request, 'info',
                  _('Your changes was saved'))
            return HTTPFound(request.route_url('home'))

    person = schema.serialize(user)

    total_fields = len(schema.children)
    filled_fields = len(person.keys())

    return {
        'person': person,
        'form': form,
        'profile_filled': (filled_fields / total_fields) * 100,
    }


@view_config(route_name='help')
def help(request):
    # We don't want to mess up the gettext .po file
    # with a lot of strings which don't belong to the
    # application interface.
    #
    # We consider the HELP as application content
    # so we simple use a different template for each
    # language. When a new locale is added to the
    # application it needs to translate the .po files
    # as well as this template

    locale_name = get_locale_name(request)
    template = 'eduiddashboard:templates/help-%s.jinja2' % locale_name

    return render_to_response(template, {}, request=request)


@view_config(route_name='token-login', request_method='POST')
def token_login(context, request):
    email = request.POST.get('email')
    token = request.POST.get('token')
    shared_key = request.registry.settings.get('auth_shared_secret')

    next_url = request.POST.get('next_url', '/')

    if verify_auth_token(shared_key, email, token):
        # Do the auth
        am = get_am(request)
        user = am.get_user_by_field('email', email)
        request.session['email'] = email
        request.session['user'] = user
        request.session['loa'] = 5
        remember_headers = remember(request, email)
        return HTTPFound(location=next_url, headers=remember_headers)
    else:
        # Show and error, the user can't be logged
        return HTTPBadRequest()
