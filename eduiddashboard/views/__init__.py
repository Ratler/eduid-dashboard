import json

from pyramid.httpexceptions import HTTPOk
from pyramid.response import Response

from pyramid_deform import FormView

from eduiddashboard.forms import BaseForm


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
        raise HTTPOk('', body_template=' ', headers=[
            ('X-Relocate', location),
        ])


class BaseActionsView(object):

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


class HTTPXRelocate(HTTPOk):

    empty_body = True

    def __init__(self, new_location, **kwargs):
        super(HTTPXRelocate, self).__init__('', headers=[
            ('X-Relocate', new_location),
        ])
