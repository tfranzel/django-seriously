from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UserCreationForm(DjangoUserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        required=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        required=False,
        help_text=_("Enter the same password as before, for verification."),
    )
    no_password = forms.BooleanField(
        label=_("Create user without password"),
        required=False,
        help_text=_("Sets an invalid password"),
    )

    def _post_clean(self):
        super()._post_clean()  # type: ignore
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)
        elif self.cleaned_data.get("no_password"):
            if self.cleaned_data.get("password1") or self.cleaned_data.get("password2"):
                self.add_error(
                    "password1", _("Cannot set password when no password is requested")
                )
                self.add_error(
                    "password2", _("Cannot set password when no password is requested")
                )
        else:
            for f in ["no_password", "password1", "password2"]:
                self.add_error(f, _("Either password or flag must be set"))

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["no_password"]:
            user.set_unusable_password()
        else:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class MinimalUserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "no_password"),
            },
        ),
    )
    readonly_fields = ("id",)
    list_display = ("email", "last_login", "is_staff", "is_superuser")
    search_fields = ("email",)
    ordering = ("email",)
