## Emails form

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from eduid_am.tasks import update_attributes

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.models import Email

from eduiddashboard.views import BaseFormView


@view_config(route_name='emails', permission='edit',
             renderer='templates/emails-form.jinja2')
class EmailsView(BaseFormView):
    """
    Provide the handler to emails
        * GET = Rendering template
        * POST = Creating or modifing emails,
                    return status and flash message
    """

    schema = Email()
    route = 'emails'

    buttons = ('add', 'verify', 'remove', 'set_primary')

    bootstrap_form_style = 'form-inline'

    def appstruct(self):
        return {}

    def get_template_context(self):
        context = super(EmailsView, self).get_template_context()

        context.update({
            'emails': self.user['emails'],
        })

        return context

    def add_success(self, emailform):
        newemail = self.schema.serialize(emailform)

        # We need to add the new email to the emails list

        emails = self.user['emails']

        emails.append({
            'email': newemail['email'],
            'verified': False,
        })

        self.request.session['user'].update(emails)

        # Do the save staff

        # Insert the new user object
        # self.request.db.profiles.update({
        #     '_id': self.user['_id'],
        # }, self.user, safe=True)

        # update_attributes.delay('eduid_dashboard', str(self.user['_id']))

        self.request.session.flash(_('Your changes was saved, please, wait '
                                     'before your changes are distributed '
                                     'through all applications'),
                                   queue='forms')

    def remove_success(self, emailform):
        remove_email = self.schema.serialize(emailform)

        emails = self.user['emails']

        new_emails = []
        for email in emails:
            if email['email'] != remove_email['email']:
                new_emails.append(email)

        self.request.session['user']['emails'] = new_emails
        self.request.session['user']['email'] = new_emails[0]['email']

        # do the save staff

        self.request.session.flash(_('Your changes was saved, please, wait '
                                     'before your changes are distributed '
                                     'through all applications'),
                                   queue='forms')

    def verify_success(self, emailform):
        email = self.schema.serialize(emailform)

        # do the email verification staff

        self.request.session.flash(_('A verification email has been sent to '
                                     'the new account. Please revise your '
                                     'inbox and click on the provided link'),
                                   queue='forms')
