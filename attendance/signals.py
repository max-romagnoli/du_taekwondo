from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal
from .models import Payment, MemberSessionLink, Member

@receiver(post_delete, sender=Payment)
def recalculate_member_balance_on_delete(sender, instance, **kwargs):
    total_paid = Payment.objects.filter(member=instance.member).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    total_money_owed = MemberSessionLink.objects.filter(member=instance.member).aggregate(total=Sum('total_money'))['total'] or Decimal('0.00')

    instance.member.overdue_balance = total_money_owed - total_paid
    instance.member.save()