from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from attendance.models import Session, MemberSessionLink, Member, Payment
from django.utils.safestring import mark_safe
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

@login_required
def session_list(request):
    # Fetch all sessions, or you can filter them based on your needs
    sessions = Session.objects.all()
    
    return render(request, 'attendance/session_list.html', {'sessions': sessions})


def take_attendance(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        # Parse the data from Handsontable
        data = request.POST.get('attendance_data')
        if data:
            import json
            attendance_data = json.loads(data)

            # Process each row in the attendance data
            for row in attendance_data:
                member_id = row['member_id']
                did_short = row['did_short']
                did_long = row['did_long']

                print(attendance_data)

                # If both are checked, only "Did Long" is valid
                if did_short and did_long:
                    did_short = False
                    did_long = True

                total_money = 0
                if not total_money:
                    # If no total_money is passed, calculate it based on checkboxes
                    if did_short:
                        total_money = 2.00  # Short session = 2
                    elif did_long:
                        total_money = 3.00  # Long session = 3

                member = get_object_or_404(Member, id=member_id)

                if did_short or did_long:
                    MemberSessionLink.objects.update_or_create(
                        member=member,
                        session=session,
                        defaults={
                            'did_short': did_short,
                            'did_long': did_long,
                            'total_money': total_money
                        }
                    )
                else:
                    MemberSessionLink.objects.filter(member=member, session=session).delete()

                # Recalculate overdue balance after changes
                recalculate_overdue_balance(member)

        return redirect('session_list')

    # Existing logic for attendance data
    name_prefix = ''
    attendance_data = []

    # Fetch existing MemberSessionLink data for this session
    member_links = MemberSessionLink.objects.filter(session=session)
    for link in member_links:
        name_prefix = '[Unregistered] ' if link.member.email is None else ''
        last_name = link.member.last_name if link.member.last_name is not None else ''
        attendance_data.append([
            link.member.id,
            f'{name_prefix}{link.member.first_name} {last_name}',
            link.did_short,
            link.did_long
        ])

    # For members who don't have a session link yet, add them with default values (short and long unchecked)
    all_members = Member.objects.all()
    for member in all_members:
        if not member_links.filter(member=member).exists():
            name_prefix = '[Unregistered] ' if member.email is None else ''
            last_name = member.last_name if member.last_name is not None else ''
            attendance_data.append([member.id, f'{name_prefix}{member.first_name} {last_name}', False, False])

    # Sort the data alphabetically by name
    attendance_data.sort(key=lambda x: x[1].lower())

    # Serialize the attendance data to ensure Python booleans are converted to JavaScript booleans
    import json
    attendance_data_json = mark_safe(json.dumps(attendance_data))

    return render(request, 'attendance/take_attendance.html', {
        'session': session,
        'attendance_data': attendance_data_json
    })


def recalculate_overdue_balance(member):
    # Calculate total money owed by summing all the session links for this member
    total_money_owed = MemberSessionLink.objects.filter(member=member).aggregate(total=Sum('total_money'))['total'] or Decimal('0.00')
    total_paid = Payment.objects.filter(member=member).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    
    # Calculate the overdue amount
    overdue_amount = total_money_owed - total_paid
    
    member.overdue_balance = overdue_amount
    member.save()