from django.db import models
from decimal import Decimal

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
    

class MemberSessionLink(models.Model):

    member = models.ForeignKey('Member', on_delete=models.CASCADE)
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    did_short = models.BooleanField(default=False)
    did_long = models.BooleanField(default=False)
    total_money = models.DecimalField(max_digits=10, decimal_places=2)

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
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    month_period = models.ForeignKey(MonthPeriod, on_delete=models.SET_NULL, null=True, blank=True)         # Copyright © 2024 Iulia Negreanu
    no_sessions = models.IntegerField(null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 

    def __str__(self):
        return f'{self.member} - Payment for {self.month_period}'
    
    class Meta:
        unique_together = ['member', 'month_period']

    @property
    def total_owed(self):
        return self.amount_due - self.amount_paid
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        total_paid = sum(payment.amount_paid for payment in Payment.objects.filter(member=self.member))
        # total_due = sum(payment.amount_due for payment in Payment.objects.filter(member=self.member))

        self.member.overdue_balance = self.member.overdue_balance - total_paid
        self.member.save()