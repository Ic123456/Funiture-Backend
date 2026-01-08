from django.contrib import admin
from .models import User
# Register your models here.


class UserAdmin(admin.ModelAdmin):
    readonly_fields = ("email", "is_superuser","is_staff")
    search_fields = ("username",)
    list_filter = ("date_joined", "registration_method", "is_active", "is_verified", "is_superuser", "is_staff")
    list_display = ( "username", "email","registration_method", "is_active", "is_verified", "is_superuser", "is_staff")
    


admin.site.register(User, UserAdmin)