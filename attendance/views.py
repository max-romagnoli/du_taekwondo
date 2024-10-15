from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from attendance.models import Session, MemberSessionLink, Member
from django.utils.safestring import mark_safe
import json

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
                member_id = row[0]  # Member ID
                did_short = row[2]  # Checkbox value for "Did Short"
                did_long = row[3]   # Checkbox value for "Did Long"

                # If both are checked, only "Did Long" is valid
                if did_short and did_long:
                    did_short = False
                    did_long = True

                # Check if the total_money is passed manually or use checkbox logic
                total_money = float(row[4]) if len(row) > 4 and row[4] is not None else 0
                if not total_money:
                    # If no total_money is passed, calculate it based on checkboxes
                    if did_short:
                        total_money = 2.00  # Short session = 2
                    elif did_long:
                        total_money = 3.00  # Long session = 3

                member = get_object_or_404(Member, id=member_id)

                # Create or update the MemberSessionLink
                member_session_link, created = MemberSessionLink.objects.update_or_create(
                    member=member,
                    session=session,
                    defaults={
                        'did_short': did_short,
                        'did_long': did_long,
                        'total_money': total_money
                    }
                )

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
