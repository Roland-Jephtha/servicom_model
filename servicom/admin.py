from django.contrib import admin
from .models import User, Department, Complaint, ComplaintResponse, Feedback, Profile
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group


class CustomUserAdmin(UserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm

    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'role')
    ordering = ('username',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )
    fieldsets = (
        (None, {'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Complaint)
admin.site.register(ComplaintResponse)
admin.site.register(Feedback)
admin.site.register(Profile)


admin.site.site_header = "PTI Online Servicom System"
admin.site.site_title = " PTI Online Servicom System Admin"
admin.site.index_title = " Manage PTI Online Servicom System"


admin.site.unregister(Group)