from django.core.management.base import BaseCommand
from attendance.models import Member, MemberSessionLink, Payment
from decimal import Decimal
from django.db import models

class Command(BaseCommand):
    help = 'Update overdue balance for each member based on their session links and payments'

    def handle(self, *args, **kwargs):
        # Fetch all members
        members = Member.objects.all()

        # Iterate through each member to calculate their overdue balance
        for member in members:
            # Calculate the total money owed by summing all the session links for this member
            total_money_owed = MemberSessionLink.objects.filter(member=member).aggregate(total_owed=models.Sum('total_money'))['total_owed'] or 0.0
            total_money_owed = Decimal(total_money_owed)

            # Calculate the total amount paid by summing all the payments made by this member
            total_paid = Payment.objects.filter(member=member).aggregate(total_paid=models.Sum('amount_paid'))['total_paid'] or 0.0
            total_paid = Decimal(total_paid)

            # Calculate the overdue amount
            overdue_amount = total_money_owed - total_paid

            # Update the member's overdue_balance field
            member.overdue_balance = overdue_amount
            member.save()

            # Log the result
            self.stdout.write(self.style.SUCCESS(f"Updated overdue balance for {member.first_name} {member.last_name}: {overdue_amount}"))

