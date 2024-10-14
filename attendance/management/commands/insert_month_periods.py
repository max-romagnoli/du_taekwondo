from django.core.management.base import BaseCommand
from attendance.models import MonthPeriod

class Command(BaseCommand):
    help = 'Insert month periods from September 2024 to June 2034'

    def handle(self, *args, **kwargs):
        start_year = 2024
        start_month = 9  # September
        end_year = 2034
        end_month = 6  # June

        months = [
            "January", "February", "March", "April", "May", "June", 
            "July", "August", "September", "October", "November", "December"
        ]

        for year in range(start_year, end_year + 1):
            for month_idx in range(1, 13):
                if year == start_year and month_idx < start_month:
                    continue
                if year == end_year and month_idx > end_month:
                    break
                
                month_name = months[month_idx - 1]

                period, created = MonthPeriod.objects.get_or_create(
                    month=month_name,
                    year=year
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Successfully created: {month_name} {year}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Already exists: {month_name} {year}'))
