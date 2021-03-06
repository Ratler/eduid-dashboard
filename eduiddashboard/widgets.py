from colander import null
import colander
import deform


@colander.deferred
def permissions_widget(node, kw):
    request = kw.get('request')
    settings = request.registry.settings

    available_permissions = settings.get('available_permissions', [])
    if (len(available_permissions) > 1 and
            not isinstance(available_permissions[0], tuple)):
        available_permissions = tuple([(p, p) for p in available_permissions])

    return deform.widget.CheckboxChoiceWidget(values=available_permissions)


class MongoCheckboxWidget(deform.widget.CheckboxWidget):

    def __init__(self, true_val=True, false_val=False, **kwargs):
        super(MongoCheckboxWidget, self).__init__(true_val=true_val,
                                                  false_val=false_val,
                                                  **kwargs)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return self.false_val

        if (pstruct == self.true_val or
                (isinstance(self.true_val, bool) and
                    bool(pstruct) == self.true_val)):
            return self.true_val

        return self.false_val


class BooleanActionWidget(MongoCheckboxWidget):

    css_class = 'boolean-action-widget'
    template = 'boolean-action-widget'
    readonly_template = 'boolean-action-widget-readonly'
    readonly = True

    def get_template_values(self, field, cstruct, kw):
        values = super(BooleanActionWidget, self).get_template_values(field,
                                                                      cstruct,
                                                                      kw)

        values.update({
            'action': self.action,
            'action_title': self.action_title,
        })

        return values

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return self.false_val

        if (pstruct == self.true_val or
                (isinstance(self.true_val, bool) and
                    bool(pstruct) == self.true_val)):
            return self.true_val

        return self.false_val


class HorizontalSequenceWidget(deform.widget.SequenceWidget):

    def __init__(
            self,
            template=('horizontal-squence'),
            item_template=('horizontal-sequence_item'),
            **kwargs
    ):
        super(HorizontalSequenceWidget, self).__init__(
            item_template=item_template,
            **kwargs
        )
