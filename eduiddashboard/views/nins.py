# NINS form

import deform

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
from pyramid.i18n import get_localizer

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.models import NIN
from eduiddashboard.utils import get_icon_string, get_short_hash
from eduiddashboard.views import BaseFormView, BaseActionsView
from eduiddashboard import log

from eduiddashboard.verifications import (new_verification_code,
                                          save_as_verificated)


def get_status(user):
    """
    Check if there is exist norEduPersonNIN active
    Else:
        Check is user has pending nin in verifications collection

    return msg and icon
    """
    schema = NIN()

    completed_fields = 0
    pending_actions = None

    for field in schema.children:
        if user.get(field.name, None) is not None:
            completed_fields += 1

    nins = user.get('norEduPersonNIN', [])
    if len(nins) > 0:
        active_nin = nins[-1]
        if not active_nin.get('active', False):
            pending_actions = _('Add national identity number')
        elif not active_nin.get('verified', False):
            pending_actions = _('Validation required for national identity number')
        else:
            completed_fields += 1
    else:
        pending_actions = _('Add national identity number')

    status = {
        'completed': (completed_fields, len(schema.children) + 1)
    }
    if pending_actions:
        status.update({
            'icon': get_icon_string('warning-sign'),
            'pending_actions': pending_actions,
        })
    return status


def send_verification_code(request, user, nin, code=None):
    """
    You need to replace the call to dummy_message with the govt
    message api
    """

    if code is None:
        code = new_verification_code(request, 'norEduPersonNIN', nin, user,
                                     hasher=get_short_hash)

    language = request.context.get_preferred_language()

    request.msgrelay.nin_validator(nin, code, language)


def mark_as_verified_nin(request, user, verified_nin):
    """
        Replace old nin with the new verified nin.
    """
    if user.get('norEduPersonNIN', None) is None:
        user['norEduPersonNIN'] = [verified_nin]
    else:
        user['norEduPersonNIN'].append(verified_nin)


def post_verified_nin(request, user, verified_nin):
    """
        Function to get the official postal address from
        the government service
    """
    log.debug('Retrieving postal address from NIN service')
    log.warning('The postal addresss service communication is not implemented')


def get_tab():
    return {
        'status': get_status,
        'label': _('National identity number'),
        'id': 'nins',
    }


def get_not_verified_nins_list(self):
    active_nins = self.user.get('norEduPersonNIN', [])
    nins = []
    verifications = self.request.db.verifications
    not_verified_nins = verifications.find({
        'model_name': 'norEduPersonNIN',
        'user_oid': self.user['_id'],
    }, sort=[('timestamp', 1)])
    if active_nins:
        active_nin = active_nins[-1]
        nin_found = False
        for nin in not_verified_nins:
            if active_nin == nin['obj_id']:
                nin_found = True
            elif nin_found and not nin['verified']:
                nins.append(nin['obj_id'])
    else:
        for nin in not_verified_nins:
            if not nin['verified']:
                nins.append(nin['obj_id'])

    return nins


def get_active_nin(self):
    active_nins = self.user.get('norEduPersonNIN', [])
    if active_nins:
        return active_nins[-1]
    else:
        return None


@view_config(route_name='nins-actions', permission='edit')
class NINsActionsView(BaseActionsView):

    data_attribute = 'norEduPersonNIN'
    verify_messages = {
        'ok': _('National identity number verified'),
        'error': _('The confirmation code is invalid, please try again or request a new code'),
        'request': _('A confirmation code has been sent to your govt mailbox'),
        'placeholder': _('National identity number confirmation code'),
        'new_code_sent': _('A new confirmation code has been sent to your govt mailbox'),
    }

    get_not_verified_nins_list = get_not_verified_nins_list
    get_active_nin = get_active_nin

    def get_verification_data_id(self, data_to_verify):
        return data_to_verify[self.data_attribute]

    def verify_action(self, index, post_data):
        """ Only the active (the last one) NIN can be verified """
        # TODO Need refact
        nins = self.user.get(self.data_attribute, {})
        if index != len(nins) - 1:
            return {
                'result': 'bad',
                'message': _("The provided nin can't be verified. You only "
                             'can verify the last one'),
            }
        return super(NINsActionsView, self).verify_action(index, post_data)

    def remove_action(self, index, post_data):
        """ Only not verified nins can be removed """
        # TODO Need refact
        nins = self.get_not_verified_nins_list()

        if len(nins) > index:
            remove_nin = nins[index]
        else:
            raise HTTPNotFound("The index provides can't be found")

        verifications = self.request.db.verifications
        verifications.remove({
            'model_name': 'norEduPersonNIN',
            'obj_id': remove_nin,
            'user_oid': self.user['_id'],
            'verified': False,
        })

        return {
            'result': 'ok',
            'message': _('National identity number has been removed'),
        }

    def send_verification_code(self, data_id, code):
        send_verification_code(self.request, self.user, data_id, code)


@view_config(route_name='nins', permission='edit',
             renderer='templates/nins-form.jinja2')
class NinsView(BaseFormView):
    """
    Provide the handler to emails
        * GET = Rendering template
        * POST = Creating or modifing nins,
                    return status and flash message
    """
    schema = NIN()
    route = 'nins'

    buttons = (deform.Button(name='add',
                             title=_('Add national identity number')), )

    bootstrap_form_style = 'form-inline'

    get_not_verified_nins_list = get_not_verified_nins_list
    get_active_nin = get_active_nin

    def appstruct(self):
        return {}

    def get_template_context(self):
        """
            Take active NIN (on am profile)
            Take NINs from verifications, sorted by older and compared with
            the present active NIN.
            If they are older, then don't take it.
            If there are not verified nins newer than the active NIN, then
            take them as not verified NINs
        """
        context = super(NinsView, self).get_template_context()
        proofing_links = self.request.registry.settings.get('proofing_links',
                                                            {})
        proofing_link = proofing_links.get('nin')

        context.update({
            'nins': self.user.get('norEduPersonNIN', []),
            'not_verified_nins': self.get_not_verified_nins_list(),
            'active_nin': self.get_active_nin(),
            'proofing_link': proofing_link,
        })

        return context

    def add_success_personal(self, ninform):
        newnin = self.schema.serialize(ninform)
        newnin = newnin['norEduPersonNIN']

        self.request.session.flash(_('Changes saved'),
                                   queue='forms')

        send_verification_code(self.request, self.user, newnin)

        msg = _('A confirmation code has been sent to your govt inbox. '
                'Please click on "Pending confirmation" link below to enter.'
                'your confirmation code')

        msg = get_localizer(self.request).translate(msg)
        self.request.session.flash(msg, queue='forms')

    def add_success_other(self, ninform):
        newnin = self.schema.serialize(ninform)
        newnin = newnin['norEduPersonNIN']

        nins = self.user.get('norEduPersonNIN', [])

        nins.append(newnin)

        self.user['norEduPersonNIN'] = nins

        # Save the state in the verifications collection
        save_as_verificated(self.request, 'norEduPersonNIN',
                            self.user['_id'], newnin)

        # Do the save staff
        self.request.db.profiles.save(self.user, safe=True)

        self.context.propagate_user_changes(self.user)

        self.request.session.flash(_('Changes saved'),
                                   queue='forms')

    def add_success(self, ninform):
        if self.context.workmode == 'personal':
            self.add_success_personal(ninform)
        else:
            self.add_success_other(ninform)
