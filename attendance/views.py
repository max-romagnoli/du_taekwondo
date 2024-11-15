from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from attendance.models import Session, MemberSessionLink, Member, Payment, MonthPeriod, MessageTemplate, MessageType
from django.utils.safestring import mark_safe
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q, Case, When, IntegerField, DecimalField, Prefetch
from django.utils import timezone
from attendance.utils import send_email
import pandas as pd
from django.http import HttpResponse
from django.urls import reverse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@login_required
def homepage(request):
    return render(request, 'attendance/homepage.html')


@login_required
def session_list(request):
    # Calculate the current academic year based on today's date
    today = timezone.now()
    if today.month >= 9:  # If month is September (9) or later
        current_academic_year = f"{today.year}-{str(today.year + 1)[-2:]}"
    else:  # If month is before September, we're still in the previous academic year
        current_academic_year = f"{today.year - 1}-{str(today.year)[-2:]}"

    # Get the academic year from the request or use the current academic year as default
    academic_year = request.GET.get('academic_year', current_academic_year)

    # Retrieve all distinct academic years for the dropdown
    academic_years = MonthPeriod.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')

    # Filter MonthPeriods based on selected academic year
    month_periods = MonthPeriod.objects.filter(academic_year=academic_year)

    # Group sessions by month period and annotate short and long attendee counts
    session_data = []
    for period in month_periods:
        sessions = Session.objects.filter(month_period=period).annotate(
            short_count=Count('membersessionlink', filter=Q(membersessionlink__did_short=True)),
            long_count=Count('membersessionlink', filter=Q(membersessionlink__did_long=True))
        ).order_by('date')
        session_data.append({
            'period': period, 
            'sessions': [
                {
                    'date': session.date,
                    'day_name': session.date.strftime('%A'),  # Get day name
                    'short_count': session.short_count,
                    'long_count': session.long_count,
                    'id': session.id,
                }
                for session in sessions
            ]
        })

    context = {
        'academic_years': academic_years,
        'selected_academic_year': academic_year,
        'session_data': session_data
    }
    return render(request, 'attendance/session_list.html', context)


@login_required
def reminders(request):
    month_periods = MonthPeriod.objects.all()
    return render(request, 'attendance/reminders.html', {'month_periods': month_periods})

@login_required
def member_records(request):
    today = timezone.now()
    if today.month >= 9:
        current_academic_year = f"{today.year}-{str(today.year + 1)[-2:]}"
    else:
        current_academic_year = f"{today.year - 1}-{str(today.year)[-2:]}"

    selected_academic_year = request.GET.get('academic_year', current_academic_year)

    academic_years = MonthPeriod.objects.values_list('academic_year', flat=True).distinct().order_by('academic_year')

    month_periods = MonthPeriod.objects.filter(academic_year=selected_academic_year).order_by('id')

    members = Member.objects.prefetch_related(
        Prefetch(
            'payments',
            queryset=Payment.objects.filter(month_period__in=month_periods),
            to_attr='filtered_payments'
        )
    ).order_by('first_name', 'last_name')

    member_data = []
    for member in members:
        row = {'member': member, 'payments': []}
        for month in month_periods:
            payment = next(
                (p for p in member.filtered_payments if p.month_period == month),
                None
            )
            if payment:
                row['payments'].append({
                    'month_amount_due': payment.month_amount_due,
                    'month_no_sessions': payment.month_no_sessions,
                    'amount_paid': payment.amount_paid,
                })
            else:
                row['payments'].append(None)  # No payment registered
        member_data.append(row)

    return render(request, 'attendance/member_records.html', {
        'academic_years': academic_years,
        'selected_academic_year': selected_academic_year,
        'month_periods': month_periods,
        'member_data': member_data,
    })


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


def email_setup(request, month_period_id):
    month_period = get_object_or_404(MonthPeriod, id=month_period_id)
    templates = MessageTemplate.objects.filter(month_period=month_period).order_by(
        Case(
            When(message_type__type='current_month', then=0),
            When(message_type__type='current_month_overdue', then=1),
            When(message_type__type='no_sessions', then=2),
            When(message_type__type='no_sessions_overdue', then=3),
            default=4,
            output_field=IntegerField()
        )
    )

    # Create default templates if they don't exist
    if templates.count() < MessageType.objects.count():
        for message_type in MessageType.objects.all().order_by(
            Case(
                When(type='current_month', then=0),
                When(type='current_month_overdue', then=1),
                When(type='no_sessions', then=2),
                When(type='no_sessions_overdue', then=3),
                default=4,
                output_field=IntegerField()
            )
        ):
            if not templates.filter(message_type=message_type).exists():
                # Determine the subject based on the type
                if message_type.type == 'other':
                    subject = ''
                else:
                    subject = f'{month_period} Taekwondo Fees'

                # Create the MessageTemplate
                MessageTemplate.objects.create(
                    short_title=message_type.display_name,
                    message_type=message_type,
                    subject=subject,
                    body=message_type.default_body,
                    month_period=month_period
                )
        templates = MessageTemplate.objects.filter(month_period=month_period)

    if request.method == 'POST':
        for template in templates:
            template.subject = request.POST.get(f'{template.message_type.type}_subject', template.subject)
            template.body = request.POST.get(f'{template.message_type.type}_body', template.body)
            template.save()

        return redirect(reverse('email_preview', args=[month_period_id]))

    return render(request, 'attendance/email_setup.html', {
        'month_period': month_period,
        'templates': templates,
    })


def email_preview(request, month_period_id):
    month_period = get_object_or_404(MonthPeriod, id=month_period_id)
    members = Member.objects.all().order_by('first_name', 'last_name')
    templates = MessageTemplate.objects.filter(month_period=month_period)
    
    email_data = []

    for member in members:

        # TODO: for testing only
        # if not member.email == 'negreani@tcd.ie' and not member.email == 'maxxromagnoli@gmail.com':
        #     continue

        if not member.email:
            continue

        member_sessions = MemberSessionLink.objects.filter(
            member=member,
            session__month_period=month_period
        ).filter(
            Q(did_short=True) | Q(did_long=True)
        )

        attended_sessions = member_sessions.count()

        # TODO: add a configuration model
        # Calculate amount due based on sessions attended this month
        gross_month_amount_due = Decimal(sum(
            2.00 if session.did_short else 3.00 if session.did_long else 0.00 for session in member_sessions
        ))

        # Get any payments made for the current month
        total_paid_this_month = Payment.objects.filter(
            member=member,
            month_period=month_period
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

        # Calculate the net amount due for the current month
        month_amount_due = gross_month_amount_due - total_paid_this_month

        payment, created = Payment.objects.update_or_create(
            member=member,
            month_period=month_period,
            defaults={'month_amount_due': month_amount_due}
        )

        previous_amount_due = Payment.objects.filter(
            member=member,
            month_period__year__lte=month_period.year,
            month_period__month__lt=month_period.month
        ).aggregate(
            unpaid_total=Sum(F('month_amount_due') - F('amount_paid'), output_field=DecimalField())
        )['unpaid_total'] or Decimal('0.00')

        # TODO: gets total also from next months
        # total_overdue = calculate_overdue_up_to_current_month(member, month_period)
        total_overdue = previous_amount_due + month_amount_due

        # Choose the appropriate template based on attendance and balance
        template = None
        if attended_sessions > 0:
            if previous_amount_due > 0:
                template = templates.get(message_type__type='current_month_overdue')
            else:
                template = templates.get(message_type__type='current_month')
        else:
            if previous_amount_due > 0:
                template = templates.get(message_type__type='no_sessions_overdue')
            else:
                template = templates.get(message_type__type='no_sessions')

        if template:
            message_body = generate_email(
                template.body,
                first_name=member.first_name,
                month=month_period.month,
                number_sessions=attended_sessions,
                month_amount_due=month_amount_due,
                previous_amount_due=previous_amount_due,
                total_overdue=total_overdue
            )
            email_data.append({
                'email': member.email,
                'first_name': member.first_name,
                'body': message_body,
                'number_sessions': attended_sessions,
                'month_amount_due': month_amount_due,
                'previous_amount_due': previous_amount_due,
                'total_overdue': total_overdue
            })

    if 'send_emails' in request.POST:
        for data in email_data:
            send_email(data['email'], template.subject, data['body'])
        return HttpResponse("Emails sent!")

    if 'export_emails' in request.POST:
        df = pd.DataFrame(email_data)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{month_period.month}_emails.csv"'
        df.to_csv(path_or_buf=response, index=False)
        return response

    return render(request, 'attendance/email_preview.html', {
        'month_period': month_period,
        'email_data': email_data,
        'templates': templates,
    })

def month_list(request):
    months = MonthPeriod.objects.all()
    return render(request, 'attendance/month_list.html', {'months': months})

""" def member_payment_entry(request, month_period_id):
    month_period = get_object_or_404(MonthPeriod, id=month_period_id)
    members = Member.objects.all().order_by('first_name', 'last_name')

    # Calculate overdue balance up to the current month for each member
    member_data = []
    for member in members:
        if not Payment.objects.filter(member=member, month_period=month_period).exists():
            payment = create_payment(member, month_period)

        overdue_balance = calculate_overdue_up_to_month(member, month_period)
        if overdue_balance > 0:
            amount_paid = Payment.objects.filter(
                member=member,
                month_period=month_period
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal
            member_data.append({
                'member': member,
                'overdue_balance': overdue_balance,
                'amount_paid': amount_paid
            })

    if request.method == 'POST':
        for data in member_data:
            member = data['member']
            amount_paid = request.POST.get(f'payment_{member.id}')
            if amount_paid:
                Payment.objects.update_or_create(
                    member=member,
                    month_period=month_period,
                    defaults={'amount_paid': float(amount_paid)}
                )
        return redirect('month_list')

    return render(request, 'attendance/member_payment_entry.html', {
        'month_period': month_period,
        'member_data': member_data,  # Pass member data with calculated overdue balance
    }) """

""" def member_payment_entry(request, month_period_id):
    month_period = get_object_or_404(MonthPeriod, id=month_period_id)
    members = Member.objects.filter(overdue_balance__gt=0).order_by('first_name', 'last_name')

    existing_payments = Payment.objects.filter(month_period=month_period).select_related('member')

    payment_dict = {payment.member.id: payment for payment in existing_payments}

    if request.method == 'POST':
        for member in members:
            amount_paid = request.POST.get(f'payment_{member.id}')
            if amount_paid:
                Payment.objects.update_or_create(
                    member=member,
                    month_period=month_period,
                    defaults={'amount_paid': float(amount_paid)}
                )
        return redirect('payment_entry')

    return render(request, 'attendance/member_payment_entry.html', {
        'month_period': month_period,
        'members': members,
        'payment_dict': payment_dict  # Pass the dictionary of existing payments to the template
    }) """



"""
Helpers
"""

def generate_email(template_body, **kwargs):
    """
    Generates an email body by replacing placeholders in the template with actual values.

    Parameters:
    - template_body (str): The template string containing placeholders.
    - kwargs (dict): Key-value pairs for placeholder replacements.

    Returns:
    - str: The formatted email body.
    """
    # Ensure all placeholders are formatted correctly in the template body
    for key, value in kwargs.items():
        placeholder = f'{{{key}}}'
        if placeholder in template_body:
            template_body = template_body.replace(placeholder, str(value))

    return template_body


def send_email(receiver_email, subject, body):
    # EMAIL CONFIGS
    sender_email = 'tcd.taekwondo@gmail.com'
    password = ''  # App-specific password

    # Create a MIMEMultipart object
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    # Attach the body text to the message
    message.attach(MIMEText(body, 'plain'))

    # Set up the SMTP server
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(sender_email, password)  # Login with your email and app password

        # Send the email
        server.send_message(message)
        print('Email sent successfully!')

        # Terminate the SMTP session
        server.quit()

    except Exception as e:
        print(f'Failed to send email: {e}')

""" # TODO:
def calculate_overdue_up_to_month(member, month_period):
    previous_amount_due = Payment.objects.filter(
        member=member,
        month_period__id__lt=month_period.id,
    ).aggregate(
        unpaid_total=Sum(F('month_amount_due') - F('amount_paid'), output_field=DecimalField())
    )['unpaid_total'] or Decimal('0.00')

    current_month_amount_due = Payment.objects.filter(
        member=member,
        month_period=month_period
    ).aggregate(
        unpaid_total=Sum(F('month_amount_due') - F('amount_paid'), output_field=DecimalField())
    )['unpaid_total'] or Decimal('0.00')

    total_overdue = previous_amount_due + current_month_amount_due

    return max(total_overdue, Decimal('0.00'))


def create_payment(member, month_period):

    member_sessions = MemberSessionLink.objects.filter(
            member=member,
            session__month_period=month_period
        ).filter(
            Q(did_short=True) | Q(did_long=True)
        )

    gross_month_amount_due = Decimal(sum(
        2.00 if session.did_short else 3.00 if session.did_long else 0.00 for session in member_sessions
    ))
    # Get any payments made for the current month
    total_paid_this_month = Payment.objects.filter(
        member=member,
        month_period=month_period
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
    # Calculate the net amount due for the current month
    month_amount_due = gross_month_amount_due - total_paid_this_month

    payment, created = Payment.objects.update_or_create(
        member=member,
        month_period=month_period,
        defaults={'month_amount_due': month_amount_due}
    )

    return payment """


def member_payment_entry(request, month_period_id):
    month_period = get_object_or_404(MonthPeriod, id=month_period_id)
    members = Member.objects.prefetch_related(
        Prefetch(
            'payments',
            queryset=Payment.objects.filter(month_period=month_period),
            to_attr='current_month_payments'
        ),
        Prefetch(
            'session_links',
            queryset=MemberSessionLink.objects.select_related('session')
        )
    ).order_by('first_name', 'last_name')

    # Pre-compute payments and overdue balances for members
    member_data = [
        get_member_payment_data(member, month_period)
        for member in members
    ]

    # Handle form submission
    if request.method == 'POST':
        process_payment_form(request, member_data, month_period)
        return redirect('payment_entry')

    return render(request, 'attendance/member_payment_entry.html', {
        'month_period': month_period,
        'member_data': [data for data in member_data if data['overdue_balance'] > 0],  # Only show members with overdue balances
    })


def get_member_payment_data(member, month_period):
    """
    Helper function to compute payment and overdue balance for a member.
    """
    # Create payment entry if not already exists
    payment = Payment.objects.filter(member=member, month_period=month_period).first()
    if not payment:
        payment = create_payment(member, month_period)

    overdue_balance = calculate_overdue_up_to_month(member, month_period)
    amount_paid = payment.amount_paid if payment else Decimal('0.00')

    return {
        'member': member,
        'overdue_balance': overdue_balance,
        'amount_paid': amount_paid,
    }


def calculate_overdue_up_to_month(member, month_period):
    """
    Helper function to calculate overdue balance up to a specific month for a member.
    """
    payments = Payment.objects.filter(member=member, month_period__id__lte=month_period.id)
    total_due = payments.aggregate(
        total_due=Sum(F('month_amount_due') - F('amount_paid'), output_field=DecimalField())
    )['total_due'] or Decimal('0.00')
    return max(total_due, Decimal('0.00'))


def create_payment(member, month_period):
    """
    Helper function to create a Payment object for a member for the specified month period.
    """
    member_sessions = MemberSessionLink.objects.filter(
        member=member,
        session__month_period=month_period
    ).filter(
        Q(did_short=True) | Q(did_long=True)
    )

    gross_month_amount_due = sum(
        Decimal('2.00') if session.did_short else Decimal('3.00')
        for session in member_sessions
    )

    payment, created = Payment.objects.update_or_create(
        member=member,
        month_period=month_period,
        defaults={'month_amount_due': gross_month_amount_due}
    )

    return payment


def process_payment_form(request, member_data, month_period):
    """
    Helper function to process payment data submitted in the form.
    """
    for data in member_data:
        member = data['member']
        amount_paid = request.POST.get(f'payment_{member.id}')
        if amount_paid:
            Payment.objects.update_or_create(
                member=member,
                month_period=month_period,
                defaults={'amount_paid': float(amount_paid)}
            )
