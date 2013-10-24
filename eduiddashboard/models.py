import re

import pycountry

import colander
import deform

from eduiddashboard.i18n import TranslationString as _
from eduiddashboard.validators import (EmailUniqueValidator,
                                       EmailExistsValidator,
                                       EmailOrUsernameExistsValidator,
                                       ResetPasswordCodeExistsValidator,
                                       PasswordValidator,
                                       OldPasswordValidator,
                                       PermissionsValidator,
                                       NINUniqueValidator)

from eduiddashboard.widgets import permissions_widget


SEARCHER_ATTTRIBUTE_TYPES = [
    (u'mail', _('email')),
    (u'mobile', _('phone mobile number')),
    (u'norEduPersonNIN', _('NIN')),
]


class BooleanMongo(colander.Boolean):

    def __init__(self, false_choices=('False', 'false', '', False),
                 true_choices=('True', 'true', True),
                 false_val=False,
                 true_val=True):
        super(BooleanMongo, self).__init__(false_choices, true_choices,
                                           false_val, true_val)


class Email(colander.MappingSchema):
    mail = colander.SchemaNode(colander.String(),
                               validator=colander.All(colander.Email(),
                                                      EmailUniqueValidator()),
                               title=_('email'),
                               widget=deform.widget.TextInputWidget(mask=_('Email address')))


class NIN(colander.MappingSchema):
    norEduPersonNIN = colander.SchemaNode(
        colander.String(),
        title=_('Swedish personal identity number'),
        validator=colander.All(
            colander.Regex(
                regex=re.compile('[0-9]{12}'),
                msg=_('The Swedish personal identity number consists of 12 digits')
            ),
            NINUniqueValidator()
        )
    )


@colander.deferred
def preferred_language_widget(node, kw):
    request = kw.get('request')
    available_languages = request.registry.settings.get('available_languages')

    lang_choices = []
    for lang in available_languages:
        lang_obj = pycountry.languages.get(alpha2=lang)
        lang_choices.append((lang, lang_obj.name))

    return deform.widget.SelectWidget(values=lang_choices)


class Person(colander.MappingSchema):
    givenName = colander.SchemaNode(colander.String(),
                                    readonly=True,
                                    title=_('Given name'))
    sn = colander.SchemaNode(colander.String(),
                             title=_('Surname'))
    displayName = colander.SchemaNode(colander.String(),
                                      title=_('Display name'))
    preferredLanguage = colander.SchemaNode(colander.String(),
                                            title=_('Preferred language'),
                                            missing='',
                                            widget=preferred_language_widget)


class Passwords(colander.MappingSchema):

    old_password = colander.SchemaNode(colander.String(),
                                       title=_('Current password'),
                                       widget=deform.widget.PasswordWidget(size=20),
                                       validator=OldPasswordValidator())
    new_password = colander.SchemaNode(colander.String(),
                                       title=_('New password'),
                                       widget=deform.widget.PasswordWidget(size=20),
                                       validator=PasswordValidator())
    new_password_repeated = colander.SchemaNode(colander.String(),
                                                title=_('Confirm new password'),
                                                widget=deform.widget.PasswordWidget(size=20))

    def validator(self, node, data):
        if data['new_password'] != data['new_password_repeated']:
            raise colander.Invalid(node,
                                   _("Passwords don't match"))


class EmailResetPassword(colander.MappingSchema):

    email_or_username = colander.SchemaNode(
      colander.String(),
      title=_("Enter your email address or your eduID username"),
      validator=colander.All(
        EmailOrUsernameExistsValidator(),
      )
    )


class NINResetPassword(colander.MappingSchema):

    # norEduPersonNIN = colander.SchemaNode(
    #     colander.String(),
    #     title=_('personal identity number (NIN)'),
    #     validator=colander.All(
    #         colander.Regex(
    #             regex=re.compile('[0-9]{12}'),
    #             msg=_('The personal identity number consists of 12 digits')
    #         ),
    #         NINExistsValidator(),
    #     )
    # )
    email_or_username = colander.SchemaNode(
      colander.String(),
      title=_("Enter your email address or your eduID username"),
      validator=colander.All(
        EmailOrUsernameExistsValidator(),
      )
    )

class ResetPasswordEnterCode(colander.MappingSchema):

    code = colander.SchemaNode(
        colander.String(),
        title=_('Confirmation code'),
        validator=colander.All(
            ResetPasswordCodeExistsValidator(),
        )
    )


class ResetPasswordStep2(colander.MappingSchema):
    new_password = colander.SchemaNode(colander.String(),
                                       widget=deform.widget.PasswordWidget(size=20),
                                       validator=PasswordValidator())
    new_password_repeated = colander.SchemaNode(colander.String(),
                                                widget=deform.widget.PasswordWidget(size=20))

    def validator(self, node, data):
        if data['new_password'] != data['new_password_repeated']:
            raise colander.Invalid(node,
                                   _("Passwords don't match"))


class PostalAddress(colander.MappingSchema):
    address = colander.SchemaNode(colander.String(), title=_('Address'))
    locality = colander.SchemaNode(colander.String(), title=_('City'))
    postalCode = colander.SchemaNode(colander.String(), title=_('Postal code'),
                                     validator=colander.Length(min=5, max=6))
    country = colander.SchemaNode(colander.String(), title=_('Country'))


class Mobile(colander.MappingSchema):
    mobile = colander.SchemaNode(colander.String(),
                                 validator=colander.Regex(
                                    r'^\+[\d ]+$',
                                    msg=_('Invalid telephone number. It must be written using international notation, starting with "+".'),
                                 ),
                                 title=_('mobile'),
                                 widget=deform.widget.TextInputWidget(mask=_('Mobile phone number')))


class Permissions(colander.Schema):
    eduPersonEntitlement = colander.SchemaNode(colander.List(),
                                               title='',
                                               validator=PermissionsValidator(),
                                               missing=[],
                                               default=[],
                                               widget=permissions_widget)


class UserSearcher(colander.MappingSchema):

    text = colander.SchemaNode(colander.String(),
                               title=_('text'),
                               description=_('the exact match text for the '
                                             'attribute type selected for '
                                             'search')
                               )

    attribute_type = colander.SchemaNode(
        colander.String(),
        title=_('attribute type'),
        description=_('Select the attribute to search'),
        default='mail',
        widget=deform.widget.RadioChoiceWidget(
            values=SEARCHER_ATTTRIBUTE_TYPES,
            inline=True
        )
    )
