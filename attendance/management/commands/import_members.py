import pandas as pd
from django.core.management.base import BaseCommand
from attendance.models import Member

class Command(BaseCommand):
    help = 'Import members from an Excel sheet into the database'

    def handle(self, *args, **kwargs):
        excel_file = './attendance/data/attendance_24_25.xlsx'  # You need to adjust this path
        
        df = pd.read_excel(excel_file, sheet_name='September')

        # Iterate through the rows in the DataFrame
        for index, row in df.iterrows():
            # Create a new User for each row
            if pd.notna(row['first_name']):
                first_name = row['first_name']
                last_name = row['surname'] if pd.notna(row['surname']) else None
                email = row['email'] if pd.notna(row['email']) else None
                member, created = Member.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )

                # Print confirmation
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created member: {member.first_name} {member.last_name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Member already exists: {member.first_name} {member.last_name}"))
