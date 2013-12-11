import colander

from eduiddashboard.userdb import UserDB

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.vccs import check_password


PASSWORD_MIN_LENGTH = 5


class OldPasswordValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        old_password = value

        user = request.session['user']
        # Load user from database to ensure we are working on an up-to-date set of credentials.
        user = request.userdb.get_user_by_oid(user['_id'])
        # XXX if we saved user['passwords'] to node.bindings.request['user']['passwords'] here,
        # we could possibly avoid doing the same refresh again when changing passwords
        # (in PasswordsView.save_success()).

        vccs_url = request.registry.settings.get('vccs_url')
        password = check_password(vccs_url, old_password, user)
        if not password:
            err = _('Current password is incorrect')
            raise colander.Invalid(node, err)


class PasswordValidator(object):
    """ Validator which check the security level of the password """

    def __call__(self, node, value):
        if len(value) < PASSWORD_MIN_LENGTH:
            err = _('The password is too short, minimum length is ${len}',
                    mapping={'len': PASSWORD_MIN_LENGTH})
            raise colander.Invalid(node, err)


class PermissionsValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        available_permissions = request.registry.settings.get('available_permissions')
        for item in value:
            if item not in available_permissions:
                raise colander.Invalid(
                    node,
                    _('The permission selected is not available')
                )


class EmailUniqueValidator(object):

    def __call__(self, node, value):

        request = node.bindings.get('request')

        if 'add' in request.POST:
            if request.userdb.exists_by_field('mailAliases.email', value):
                raise colander.Invalid(node,
                                       _("This email address is already in use"))

        elif 'verify' in request.POST or 'setprimary' in request.POST:
            if not request.userdb.exists_by_field('mailAliases.email', value):
                raise colander.Invalid(node,
                                       _("This email address is available"
                                         ))

        elif 'remove' in request.POST:
            email_discovered = False
            for emaildict in request.session['user']['mailAliases']:
                if emaildict['email'] == value:
                    email_discovered = True
                    break
            if not email_discovered:
                raise colander.Invalid(node,
                                       _("Email address does not exist"))

            if len(request.session['user']['mailAliases']) <= 1:
                raise colander.Invalid(node,
                                       _("At least one email is required"))


class EmailExistsValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        try:
            request.userdb.get_user_by_email(value)
        except UserDB.UserDoesNotExist:
            raise colander.Invalid(node,
                                   _("Email address does not exist"))


class MobilePhoneUniqueValidator(object):

    def __call__(self, node, value):

        request = node.bindings.get('request')

        if 'add' in request.POST:
            if request.userdb.exists_by_field('mobile.mobile', value):
                raise colander.Invalid(node,
                                       _("This mobile phone was already registered"))


class EmailOrUsernameExistsValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        try:
            request.userdb.get_user_by_username(value)
        except UserDB.UserDoesNotExist:
            try:
                request.userdb.get_user_by_email(value)
            except UserDB.UserDoesNotExist:
                raise colander.Invalid(node,
                                       _("Username or email address does not exist"))


class NINExistsValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        try:
            request.userdb.get_user_by_nin(value)
        except UserDB.UserDoesNotExist:
            raise colander.Invalid(node,
                                   _("This national identity number does not exist, is not verified or is not active"))


class NINUniqueValidator(object):

    def __call__(self, node, value):
        """
            Check if the NIN was not already registered and verified by any user
            Check if the NIN was not already registered by the present user in the
                verifications process.
        """

        request = node.bindings.get('request')

        if request.userdb.exists_by_filter({
            'norEduPersonNIN': value,
        }):
            raise colander.Invalid(
                node,
                _("This national identity number is already in use"))

        verifications = request.db.verifications

        if verifications.find({
            'obj_id': value,
            'model_name': 'norEduPersonNIN',
            'verified': False
        }).count() > 0:
            raise colander.Invalid(node, _('This national identity number is '
                                   'already in use by you'))


class ResetPasswordCodeExistsValidator(object):

    def __call__(self, node, value):
        request = node.bindings.get('request')
        if not request.db.reset_passwords.find_one({'hash_code': value}):
            raise colander.Invalid(node,
                                   _("The entered code does not exist"))
