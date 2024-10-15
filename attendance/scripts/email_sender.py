import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(receiver_email, subject, body):
    # EMAIL CONFIGS                     # TODO: setup Iulia's email configs
    sender_email = 'stagent9@gmail.com'
    password = 'hqtj uxbi qrwf rtxg'  # App-specific password

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
