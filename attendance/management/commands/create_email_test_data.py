# attendance/management/commands/create_test_data.py
from django.core.management.base import BaseCommand
from attendance.models import MonthPeriod, Member, MemberSessionLink, Payment, Session
from datetime import date

class Command(BaseCommand):
    help = 'Create test data for the attendance app'

    def handle(self, *args, **kwargs):
        # Create the "Ginevro 3000" MonthPeriod
        ginevro_3000, created = MonthPeriod.objects.get_or_create(month='Ginevro', year=3000)
        if created:
            self.stdout.write(self.style.SUCCESS('MonthPeriod "Ginevro 3000" created successfully.'))

        # Create the members
        iulia, created = Member.objects.get_or_create(first_name='Iulia', last_name='Negreanu', email='negreani@tcd.ie')
        maxx, created = Member.objects.get_or_create(first_name='Max', last_name='Romagnoli', email='maxxromagnoli@gmail.com')

        session1 = Session.objects.create(date=date(3000, 1, 13), month_period=ginevro_3000)

        # Create member session links for "Ginevro 3000" for both members
        for member in [iulia, maxx]:
            MemberSessionLink.objects.create(member=member, session=session1, did_short=True, total_money=2)
            self.stdout.write(self.style.SUCCESS(f'MemberSessionLink for "Ginevro 3000" created for {member.first_name} {member.last_name}.'))

        # Create member session links for October 2030
        october_2030, created = MonthPeriod.objects.get_or_create(month='October', year=2030)
        session2 = Session.objects.create(date=date(2030, 10, 1), month_period=october_2030)
        for member in [iulia, maxx]:
            for i in range(1):
                MemberSessionLink.objects.create(member=member, session=session2, did_short=True, total_money=2)
            self.stdout.write(self.style.SUCCESS(f'MemberSessionLink for "October 2030" created for {member.first_name} {member.last_name}.'))

        # Create payments for October 2030
        Payment.objects.create(member=iulia, month_period=october_2030, amount_paid=2)
        self.stdout.write(self.style.SUCCESS('Payment of 4 euros created for Iulia Negreanu for October 2030.'))

        Payment.objects.create(member=maxx, month_period=october_2030, amount_paid=2)
        self.stdout.write(self.style.SUCCESS('Payment of 6 euros created for Max Romagnoli for October 2030.'))

        self.stdout.write(self.style.SUCCESS('Test data created successfully.'))
