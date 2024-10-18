import pandas as pd
from django.core.management.base import BaseCommand
from attendance.models import Member, Payment, MonthPeriod
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create Payment objects for members based on the overdue column from the spreadsheet'

    def handle(self, *args, **kwargs):
        # Load the spreadsheet
        file_path = './attendance/data/attendance_24_25.xlsx'  # Update this to the correct file path
        df = pd.read_excel(file_path, sheet_name='September')

        # Get the September month period
        september = self.get_september_period()

        # Iterate over each row in the spreadsheet
        for index, row in df.iterrows():
            # Get member details
            email = row.get('email')
            first_name = row.get('first_name')
            overdue = Decimal(row.get('overdue', 0))  # Get overdue value
            total_money = Decimal(row.get('total_money', 0))  # Get total_money value

            # Check if overdue is 0 and different from total_money
            if overdue == 0 and overdue != total_money:
                # Identify the member using email or first name
                if pd.notna(email):
                    member = Member.objects.filter(email=email).first()
                else:
                    member = Member.objects.filter(first_name=first_name).first()

                if not member:
                    self.stdout.write(self.style.ERROR(f"Member not found: {first_name} ({email})"))
                    continue

                # Create a new payment object for September
                Payment.objects.create(
                    member=member,
                    month_period=september,
                    amount_paid=total_money,
                    amount_due=total_money
                )

                self.stdout.write(self.style.SUCCESS(f"Created payment (due {total_money}, paid {total_money}) for {member.first_name} {member.last_name} for September"))

    def get_september_period(self):
        # Utility to get or create the MonthPeriod for September 2024
        month = "September"
        year = timezone.now().year  # Adjust year if needed
        month_period, _ = MonthPeriod.objects.get_or_create(month=month, year=year)
        return month_period
