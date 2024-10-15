import csv
from django.core.management.base import BaseCommand
from attendance.models import Member
from datetime import datetime

class Command(BaseCommand):
    help = 'Import members from updated report_members_oct_2024.csv'

    def handle(self, *args, **kwargs):
        file_path = './attendance/data/report_members_oct_2024.csv'  # Update this path as needed
        
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Extract necessary fields from the CSV
                first_name = row['Members name']  # 'Members name' column in CSV
                last_name = row['Members surname']  # 'Members surname' column in CSV
                email = row['Email']  # 'Email' column in CSV

                # Parse registration date from 'Registered date & time' column
                registration_date_str = row['Registered date & time']
                registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d %H:%M:%S')

                # Create or update Member record
                member, created = Member.objects.update_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    defaults={
                        'email': email,
                        'registration_date': registration_date
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created new member: {first_name} {last_name}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"Updated member: {first_name} {last_name}"))
