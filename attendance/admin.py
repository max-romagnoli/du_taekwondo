from django.contrib import admin
from .models import *

class MemberPaymentInline(admin.TabularInline):
    model = Payment
    extra = 1

class MemberSessionLinkInline(admin.TabularInline):
    model = MemberSessionLink
    extra = 1 

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'overdue_balance')
    search_fields = ('first_name', 'last_name', 'email')
    ordering = ('first_name', 'last_name')

    inlines = [MemberSessionLinkInline, MemberPaymentInline]

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
    ordering = ('-session', 'member__first_name', 'member__last_name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['date_paid', 'member', 'month_period', 'month_no_sessions', 'month_amount_due', 'amount_paid',]
    list_filter = ['month_period',]
    search_fields = ['member__first_name', 'member__last_name',]

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    pass

@admin.register(MessageType)
class MessageTypeAdmin(admin.ModelAdmin):
    pass