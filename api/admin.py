from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

User = get_user_model()

class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    # The fields to be used in displaying the User model.
    list_display = ("email", "first_name", "surname", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")

    # Fields to display when editing a user
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "surname")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    # Fields to display when creating a user in the admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "surname", "password1", "password2", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email", "first_name", "surname")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")


admin.site.register(User, UserAdmin)
