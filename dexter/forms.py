from flask_wtf import Form as BaseForm
from wtforms import SelectMultipleField, widgets, SelectField as WTFSelectField
from wtforms.fields.html5 import IntegerField as WTFIntegerField

class StripFilter():
    def __call__(self, value):
        if value is not None and hasattr(value, 'strip'):
            return value.strip()
        else:
            return value


class Form(BaseForm):
    """ A form that strips the values of all its fields. """
    _decorated = False

    def __init__(self, *args, **kwargs):
        if 'obj' in kwargs:
            self._obj = kwargs['obj']
        super(Form, self).__init__(*args, **kwargs)

    def process(self, *args, **kwargs):
        if not self._decorated:
            self._decorated = True
            for field in self._fields.itervalues():
                field.filters = [StripFilter()] + list(field.filters)

        super(Form, self).process(*args, **kwargs)


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class IntegerField(WTFIntegerField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                if valuelist[0]:
                    self.data = int(valuelist[0])
                else:
                    self.data = None
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid integer value'))

class SelectField(WTFSelectField):
    def populate_obj(self, obj, name):
        super(WTFSelectField, self).populate_obj(obj, name)

        if hasattr(obj, name):
            val = getattr(obj, name, None)
            if val == '' or val == 'None':
                setattr(obj, name, None)
