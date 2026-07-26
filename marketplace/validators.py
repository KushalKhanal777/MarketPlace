import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """
    Validate that the password meets strong password criteria.
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (!@#$%^&*(),.?":{}|<>)
    """

    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _('Password must be at least 8 characters long.'),
                code='password_too_short',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('Password must contain at least 1 uppercase letter.'),
                code='password_no_uppercase',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _('Password must contain at least 1 lowercase letter.'),
                code='password_no_lowercase',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('Password must contain at least 1 digit.'),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _('Password must contain at least 1 special character (!@#$%^&*(),.?":{}|<>).'),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            'Your password must contain at least 8 characters, '
            'including uppercase, lowercase, digit, and special character.'
        )
