from django.db import models
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from simple_history.models import HistoricalRecords
from datetime import date, timedelta
import calendar
from django.core.validators import MinValueValidator

class Member(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True, blank=True)
    overdue_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    registration_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['first_name', 'last_name', 'email']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    

class MonthPeriod(models.Model):

    month = models.CharField()
    year = models.PositiveIntegerField()
    academic_year = models.CharField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['month', 'year'], name='unique_month_year')
        ]
        verbose_name = 'Month'
        verbose_name_plural = 'Months'

    def __str__(self):
        return f"{self.month} {self.year}"
    

class Session(models.Model):

    date = models.DateField()
    month_period = models.ForeignKey('MonthPeriod', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Session on {self.date} ({self.month_period})"
    
    class Meta:
        unique_together = ('date', 'month_period')
    

class MemberSessionLink(models.Model):

    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='session_links')
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    did_short = models.BooleanField(default=False)
    did_long = models.BooleanField(default=False)
    total_money = models.DecimalField(max_digits=10, decimal_places=2)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Member - Session Link'
        verbose_name_plural = 'Member - Session Links'
        unique_together = ['member', 'session']

    # TODO: should be done frontend side
    """ def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        old_overdue = Decimal(self.member.overdue_balance)
        added_money = Decimal(self.total_money)
        self.member.overdue_balance = old_overdue + added_money
        self.member.save() """

    def __str__(self):
        return f'{self.member} attended {self.session}'
    

class Payment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.SET_NULL, null=True, blank=True)         # Copyright © 2024 Iulia Negreanu
    month_amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    month_no_sessions = models.IntegerField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_created = models.DateTimeField(auto_now_add=True)
    date_paid = models.DateTimeField(null=True, blank=True)
    validators=[MinValueValidator(0.00)]

    def __str__(self):
        return f'{self.member} - Payment for {self.month_period}'
    
    class Meta:
        unique_together = ['member', 'month_period']

    def save(self, *args, **kwargs):
        member_sessions = MemberSessionLink.objects.filter(
            member=self.member,
            session__month_period=self.month_period
        ).filter(Q(did_short=True) | Q(did_long=True))

        self.month_no_sessions = member_sessions.count()
        self.month_amount_due = Decimal(sum(
            2.00 if session.did_short else 3.00 if session.did_long else 0.00 for session in member_sessions
        ))

        self.recalculate_member_balance()

        super().save(*args, **kwargs)

    def recalculate_member_balance(self):
        total_paid = Payment.objects.filter(member=self.member).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        total_money_owed = MemberSessionLink.objects.filter(member=self.member).aggregate(total=Sum('total_money'))['total'] or Decimal('0.00')

        self.member.overdue_balance = total_money_owed - total_paid
        self.member.save()


class MessageType(models.Model):
    MESSAGE_TYPES = [
        ('current_month', 'Member Attended Sessions in Month'),
        ('current_month_overdue', 'Member Attended Sessions in Month + Overdue'),
        ('no_sessions', 'Member Did Not Attend Sessions in Month'),
        ('no_sessions_overdue', 'Member Did Not Attend Sessions in Month + Overdue'),
        ('other', 'Other')
    ]

    type = models.CharField(max_length=50, choices=MESSAGE_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    default_body = models.TextField()

    def __str__(self):
        return self.display_name
    
    class Meta:
        verbose_name = 'Message Type'
        verbose_name_plural = 'Message Types'


class MessageTemplate(models.Model):
    month_period = models.ForeignKey('MonthPeriod', on_delete=models.SET_NULL, null=True, blank=True)
    message_type = models.ForeignKey(MessageType, on_delete=models.CASCADE)
    short_title = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return f'{self.month_period} - {self.message_type.display_name}'

    class Meta:
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'


""" class MessageTemplate(models.Model):
    subject = models.CharField(max_length=200)
    body = models.TextField()
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Template for {self.month_period.month} {self.month_period.year}"
    
    class Meta:
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates' """