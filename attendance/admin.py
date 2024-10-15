from django.contrib import admin
from .models import *

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(MonthPeriod)
class MonthPeriodAdmin(admin.ModelAdmin):

    class SessionInline(admin.TabularInline):
        model = Session
        extra = 1

    ordering = ('id',)
    inlines = [SessionInline]

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'month_period')
    list_filter = ('month_period', 'date')
    search_fields = ('month_period__month', 'month_period__year')

@admin.register(MemberSessionLink)
class MemberSessionAdmin(admin.ModelAdmin):
    list_display = ('member', 'session', 'did_short', 'did_long', 'total_money')
    list_filter = ('did_short', 'did_long')
    search_fields = ('member__first_name', 'member__last_name', 'session__date')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'month_period', 'amount_due', 'amount_paid',]
    list_filter = ['month_period',]
    search_fields = ['member__first_name', 'member__last_name',]