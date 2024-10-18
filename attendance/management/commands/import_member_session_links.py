import pandas as pd
from django.core.management.base import BaseCommand
from attendance.models import Member, Session, MemberSessionLink, MonthPeriod
from datetime import datetime

class Command(BaseCommand):
    help = 'Create MemberSessionLink entries from the Excel file'

    def handle(self, *args, **kwargs):
        # Load the Excel file
        file_path = './attendance/data/attendance_24_25.xlsx'  # Update this to the correct file path
        df = pd.read_excel(file_path, sheet_name='October (2)')

        # The header for sessions (dates)
        session_dates = df.columns[6:9]  # Assuming first 6 columns are member details

        # Loop through each row in the dataframe (representing a member)
        for index, row in df.iterrows():

            # Identify the member by email or first_name
            email = row['email']
            first_name = row['first_name']

            if pd.notna(email):  # If email exists, use it
                member = Member.objects.filter(email=email).first()
            else:  # Otherwise, use first_name
                member = Member.objects.filter(first_name=first_name, email__isnull=True).first()

            if not member:
                self.stdout.write(self.style.ERROR(f"Member not found: {first_name} ({email})"))
                continue

            # Loop through each session (date columns)
            for date_str in session_dates:
                # Parse session date
                # print(date_str)
                # session_date = pd.to_datetime(date_str, dayfirst=True).date()

                try:
                    session_date = pd.to_datetime(date_str, format='%d/%m/%Y').date()
                except ValueError:
                    self.stdout.write(self.style.ERROR(f"Error parsing date: {date_str}"))
                    continue

                # Check the attendance value (e.g., 2 or 3)
                attendance_value = row[date_str]

                if pd.notna(attendance_value) and attendance_value > 0:
                    # Find or create the Session
                    session, created = Session.objects.get_or_create(
                        date=session_date,
                        defaults={'month_period': self.get_month_period(session_date)}
                    )

                    # Determine the session type based on the attendance value
                    did_short = attendance_value == 2
                    did_long = attendance_value == 3

                    # Create or update MemberSessionLink
                    member_session_link, created = MemberSessionLink.objects.update_or_create(
                        member=member,
                        session=session,
                        defaults={
                            'did_short': did_short,
                            'did_long': did_long,
                            'total_money': attendance_value
                        }
                    )

                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created MemberSessionLink for {member} on {session_date}"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"Updated MemberSessionLink for {member} on {session_date}"))

    def get_month_period(self, session_date):
        # Utility to get the MonthPeriod object for the given date
        month = session_date.strftime('%B')  # Full month name
        year = session_date.year
        month_period, _ = MonthPeriod.objects.get_or_create(month=month, year=year)
        return month_period
