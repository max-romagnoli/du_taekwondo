from django.core.management.base import BaseCommand
from attendance.models import Payment, MonthPeriod
from django.db.models import Q


class Command(BaseCommand):
    help = 'Recalculate month_amount_due, month_no_sessions, and overdue_balance for all Payments in October and November 2024'

    def handle(self, *args, **kwargs):
        # Fetch MonthPeriod objects for October and November 2024
        months = MonthPeriod.objects.filter(month__in=['September'], year=2024)

        if not months.exists():
            self.stdout.write(self.style.WARNING('No entries found for October or November 2024.'))
            return

        # Process Payments for October and November 2024
        payments = Payment.objects.filter(month_period__in=months)

        if not payments.exists():
            self.stdout.write(self.style.WARNING('No Payment entries found for October or November 2024.'))
            return

        updated_count = 0

        for payment in payments:
            # Recalculate the Payment fields and save
            payment.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully updated {updated_count} Payment entries for October and November 2024.'
        ))