## Mobile phones forms

from pyramid.view import view_config

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.models import Mobile
from eduiddashboard.utils import get_icon_string
from eduiddashboard.views import BaseFormView, BaseActionsView


def pending_verifications(user):
    """ Return a list of dicts like this:
        [{'field': 'mobile',
          'form': 'mobile',
          'msg': _('You need to verify mobile'),
        }]
    """
    for mobile in user.get('mobiles', []):
        if not mobile['verified']:
            return [{
                'field': 'mobile',
                'form': 'mobile',
                'msg': _('You have to verificate some mobile'),
            }]
    return []


def get_status(user):
    """
    Check if all mobiles are verified already

    return msg and icon
    """

    if pending_verifications(user):
        msg = _('You have to verificate some mobiles')
        return {
            'icon': get_icon_string('warning-sign'),
            'msg': msg,
            'pending_actions': msg,
            'completed': (0, 1),
        }
    return {
        'completed': (1, 1),
    }


def get_tab():
    return {
        'status': get_status,
        'label': _('Mobiles'),
        'id': 'mobiles',
    }


@view_config(route_name='mobiles-actions', permission='edit')
class MobilesActionsView(BaseActionsView):

    def remove_action(self, index, post_data):
        mobiles = self.user['mobiles']
        mobile_to_remove = mobiles[index]
        mobiles.remove(mobile_to_remove)

        self.user['mobiles'] = mobiles

        # do the save staff
        self.request.db.profiles.find_and_modify({
            '_id': self.user['_id'],
        }, {
            '$set': {
                'mobiles': mobiles,
            }
        }, safe=True)

        self.context.propagate_user_changes(self.user)

        return {
            'result': 'ok',
            'message': _('One mobile has been removed, please, wait'
                         ' before your changes are distributed '
                         'through all applications'),
        }


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

    buttons = ('add', )

    def appstruct(self):
        return {}

    def get_template_context(self):
        context = super(MobilesView, self).get_template_context()
        context.update({
            'mobiles': self.user.get('mobiles', []),
        })
        return context

    def add_success(self, mobileform):
        mobile = self.schema.serialize(mobileform)
        mobile['verified'] = False

        mobiles = self.user.get('mobiles', [])
        mobiles.append(mobile)

        # update the session data
        self.user['mobiles'] = mobiles

        # do the save staff
        self.request.db.profiles.find_and_modify({
            '_id': self.user['_id'],
        }, {
            '$push': {
                'mobiles': mobiles,
            }
        }, safe=True)

        # update the session data
        self.context.propagate_user_changes(self.user)

        self.request.session.flash(_('Your changes was saved, please, wait '
                                     'before your changes are distributed '
                                     'through all applications'),
                                   queue='forms')
