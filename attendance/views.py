from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from attendance.models import Session, MemberSessionLink, Member


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
                total_money = float(row[2]) if row[2] else 0

                member = get_object_or_404(Member, id=member_id)

                # Create or update the MemberSessionLink
                member_session_link, created = MemberSessionLink.objects.update_or_create(
                    member=member,
                    session=session,
                    defaults={'total_money': total_money}
                )

        return redirect('session_list')

    name_prefix = ''
    attendance_data = []

    # Fetch existing MemberSessionLink data for this session
    member_links = MemberSessionLink.objects.filter(session=session)
    for link in member_links:
        name_prefix = '[Unregistered] ' if link.member.email is None else ''
        last_name = link.member.last_name if link.member.last_name is not None else ''
        attendance_data.append([link.member.id, f'{name_prefix}{link.member.first_name} {last_name}', float(link.total_money)])

    # For members who don't have a session link yet, add them with default total_money = 0
    all_members = Member.objects.all()
    for member in all_members:
        if not member_links.filter(member=member).exists():
            name_prefix = '[Unregistered] ' if member.email is None else ''
            last_name = member.last_name if member.last_name is not None else ''
            attendance_data.append([member.id, f'{name_prefix}{member.first_name} {last_name}', 0])

    attendance_data.sort(key=lambda x: x[1].lower())

    return render(request, 'attendance/take_attendance.html', {
        'session': session,
        'attendance_data': attendance_data
    })
