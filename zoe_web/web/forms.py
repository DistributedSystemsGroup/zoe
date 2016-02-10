from wtforms import Form, StringField, validators


class LoginWithGuestIDForm(Form):
    guest_identifier = StringField('Guest ID', [validators.Length(min=8, max=8)])
