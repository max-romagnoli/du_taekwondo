from django.core.management.base import BaseCommand
from attendance.models import MonthPeriod

class Command(BaseCommand):
    help = 'Sets the academic year for all existing MonthPeriod records'

    def handle(self, *args, **kwargs):
        # Loop over all MonthPeriod entries to set the academic_year field
        for month_period in MonthPeriod.objects.all():
            # Determine the start year of the academic year
            start_year = month_period.year
            if month_period.month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August']:
                # Months from January to August are part of the previous academic year
                start_year -= 1

            # Format the academic year as "YYYY-YY"
            end_year_suffix = (start_year + 1) % 100
            academic_year = f"{start_year}-{end_year_suffix:02}"

            # Update the academic year field
            month_period.academic_year = academic_year
            month_period.save()

            self.stdout.write(self.style.SUCCESS(f"Set academic year {academic_year} for {month_period.month} {month_period.year}"))