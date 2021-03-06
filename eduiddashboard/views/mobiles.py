## Mobile phones forms

import deform

from pyramid.i18n import get_localizer
from pyramid.view import view_config

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.models import Mobile
from eduiddashboard.utils import get_icon_string, get_short_hash, convert_to_e_164
from eduiddashboard.verifications import new_verification_code
from eduiddashboard.views import BaseFormView, BaseActionsView


def get_status(request, user):
    """
    Check if all mobiles are verified already

    return msg and icon
    """
    mobiles = user.get_mobiles()
    pending_actions = None
    pending_action_type = ''
    verification_needed = -1

    if not mobiles:
        pending_actions = _('Add mobile phone number')
    else:
        for n, mobile in enumerate(mobiles):
            if not mobile['verified']:
                verification_needed = n
                pending_action_type = 'verify'
                pending_actions = _('A mobile phone number is pending confirmation')

    if pending_actions:
        return {
            'icon': get_icon_string('warning-sign'),
            'pending_actions': pending_actions,
            'pending_action_type': pending_action_type,
            'completed': (0, 1),
            'verification_needed': verification_needed,
        }
    return {
        'completed': (1, 1),
    }


def get_tab():
    return {
        'status': get_status,
        'label': _('Mobile phone numbers'),
        'id': 'mobiles',
    }


def send_verification_code(request, user, mobile_number, code=None):
    if code is None:
        code = new_verification_code(request, 'mobile', mobile_number, user,
                                     hasher=get_short_hash)

    user_language = request.context.get_preferred_language()

    request.msgrelay.mobile_validator(mobile_number, code, user_language)


@view_config(route_name='mobiles-actions', permission='edit')
class MobilesActionsView(BaseActionsView):
    data_attribute = 'mobile'
    verify_messages = {
        'ok': _('The mobile phone number has been verified'),
        'error': _('The confirmation code used is invalid, please try again or request a new code'),
        'request': _('A confirmation code has been sent to the mobile phone number {data}'),
        'placeholder': _('Mobile phone code'),
        'new_code_sent': _('A new confirmation code has been sent to your mobile number'),
    }

    def get_verification_data_id(self, data_to_verify):
        return data_to_verify['mobile']

    def remove_action(self, index, post_data):
        mobiles = self.user.get_mobiles()
        mobile_to_remove = mobiles[index]
        mobiles.remove(mobile_to_remove)

        self.user.set_mobiles(mobiles)

        self.user.save(self.request)

        return {
            'result': 'ok',
            'message': _('Mobile phone number was successfully removed'),
        }

    def setprimary_action(self, index, post_data):
        mobiles = self.user.get_mobiles()

        if index > len(mobiles):
            return {
                'result': 'bad',
                'message': _("That mobile phone number doesn't exists"),
            }

        if index > len(mobiles):
            return {
                'result': 'bad',
                'message': _("You need to verify that mobile phone number "
                             "before be able to set as primary"),
            }

        # set all to False, and then set the new primary to True using the index
        for mobile in mobiles:
            mobile['primary'] = False

        assert(mobiles[index]['verified'])  # double check
        mobiles[index]['primary'] = True

        self.user.set_mobiles(mobiles)
        self.user.save(self.request)

        return {
            'result': 'ok',
            'message': _('Mobile phone number was successfully made primary'),
        }

    def send_verification_code(self, data_id, code):
        send_verification_code(self.request, self.user, data_id, code)


@view_config(route_name='mobiles', permission='edit',
             renderer='templates/mobiles-form.jinja2')
class MobilesView(BaseFormView):
    """
    Change user mobiles
        * GET = Rendering template
        * POST = Creating or modifing mobiles data,
                    return status and flash message
    """

    schema = Mobile()
    route = 'mobiles'

    buttons = (deform.Button(name='add', title=_('Add mobile phone number')), )

    bootstrap_form_style = 'form-inline'

    def appstruct(self):
        return {}

    def get_template_context(self):
        context = super(MobilesView, self).get_template_context()
        context.update({
            'mobiles': self.user.get_mobiles(),
        })
        return context

    def add_success(self, mobileform):
        mobile = self.schema.serialize(mobileform)
        convert_to_e_164(self.request, mobile)
        mobile_number = mobile['mobile']
        mobile['verified'] = False
        mobile['primary'] = False

        self.user.add_mobile(mobile)
        self.user.save(self.request)

        send_verification_code(self.request, self.user, mobile_number)

        self.request.session.flash(_('Changes saved'),
                                   queue='forms')
        msg = _('A confirmation code has been sent to your mobile phone. '
                'Please click on the "Pending confirmation" link below and enter your confirmation code.')
        msg = get_localizer(self.request).translate(msg)
        self.request.session.flash(msg,
                                   queue='forms')
