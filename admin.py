from django.contrib import admin
from .models import EmergencyContact, Report

admin.site.register(EmergencyContact)
admin.site.register(Report)
from django.contrib import admin
from .models import UserProfile, HelpCenter, SOSLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    search_fields = ('user__username', 'phone')

@admin.register(HelpCenter)
class HelpCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'address')
    search_fields = ('name',)

@admin.register(SOSLog)
class SOSLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'timestamp')
    search_fields = ('user__username',)

