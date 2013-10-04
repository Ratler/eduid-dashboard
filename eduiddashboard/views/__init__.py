import json

from pyramid.httpexceptions import HTTPOk
from pyramid.response import Response

from pyramid_deform import FormView

from eduiddashboard.forms import BaseForm
from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.verifications import get_verification_code, verificate_code


def get_dummy_status(user):
    return None


class BaseFormView(FormView):
    form_class = BaseForm
    route = ''
    base_route = 'profile-editor'

    buttons = ('save', )
    use_ajax = True

    def __init__(self, context, request):
        super(BaseFormView, self).__init__(request)
        self.user = context.user
        self.context = context

        self.classname = self.__class__.__name__.lower()

        self.ajax_options = json.dumps({
            'replaceTarget': True,
            'url': context.route_url(self.route),
            'target': "div.{classname}-form-container".format(
                classname=self.classname),

        })

        self.form_options = {
            'formid': "{classname}-form".format(classname=self.classname),
            'action': context.route_url(self.route),
        }

        bootstrap_form_style = getattr(self, 'bootstrap_form_style', None)
        if bootstrap_form_style is not None:
            self.form_options['bootstrap_form_style'] = bootstrap_form_style

    def appstruct(self):
        return self.schema.serialize(self.user)

    def get_template_context(self):
        return {
            'formname': self.classname
        }

    def failure(self, e):
        context = super(BaseFormView, self).failure(e)

        context.update(self.get_template_context())

        return context

    def show(self, form):
        context = super(BaseFormView, self).show(form)

        context.update(self.get_template_context())

        return context

    def full_page_reload(self):
        location = self.request.route_path(self.base_route)
        raise HTTPXRelocate(location)


class BaseActionsView(object):
    data_attribute = None
    verify_messages = {
        'ok': _('The data has been verified'),
        'error': _('The confirmation code is not the one have been sent to your mobile phone'),
        'request': _('Please revise your inbox and fill below with the given code'),
        'placeholder': _('Verification code'),
    }

    def __init__(self, context, request):
        self.request = request
        self.context = context
        self.user = context.user

    def __call__(self):
        action = self.request.POST['action']
        action_method = getattr(self, '%s_action' % action)
        post_data = self.request.POST
        index = int(post_data['identifier'])
        result = action_method(index, post_data)
        result['action'] = action
        result['identifier'] = index
        return Response(json.dumps(result))

    def get_verification_data_code(self, data_to_verify):
        raise NotImplementedError()

    def verify_action(self, index, post_data):
        """ Common action to verificate some given data. You can override in subclasses """
        data_to_verify = self.user.get(self.data_attribute, [])[index]
        data_code = self.get_verification_data_code(data_to_verify)
        if 'code' in post_data:
            code_sent = post_data['code']
            verification_code = get_verification_code(self.request.db, self.data_attribute, data_code)
            if code_sent == verification_code['code']:
                verificate_code(self.request, self.data_attribute, code_sent)
                return {
                    'result': 'ok',
                    'message': self.verify_messages['ok'],
                }
            else:
                return {
                    'result': 'error',
                    'message': self.verify_messages['error'],
                }
        else:
            return {
                'result': 'getcode',
                'message': self.verify_messages['request'],
                'placeholder': self.verify_messages['placeholder'],
            }


class HTTPXRelocate(HTTPOk):

    empty_body = True

    def __init__(self, new_location, **kwargs):
        super(HTTPXRelocate, self).__init__('', headers=[
            ('X-Relocate', new_location),
        ])
