from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from django.utils.translation import gettext_lazy as _


class TokenChangeForm(forms.ModelForm):
    key = ReadOnlyPasswordHashField(
        label=_("Key"),
        help_text=_("Raw keys are not stored, so there is no way to see this key"),
    )
