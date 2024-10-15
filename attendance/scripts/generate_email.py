import pandas as pd
import textwrap
from email_sender import send_email

# Load the uploaded Excel file
file_path = './attendance_24_25.xlsx'
month = 'TEST_Ginevro'  # Sheet name containing the data
data = pd.read_excel(file_path, sheet_name=month)
subject = f'{month} Taekwondo Fees'

# Prepare a new dataframe to store email addresses and bodies
email_data = []

# Loop through the rows to generate the email body for each person
for index, row in data.iterrows():
    email = row['email']
    first_name = row['first_name']
    total_money = row['total_money']

    # Check if both 'first_name' and 'email' are not empty
    if pd.notna(email):
        no_sessions = row['no_sessions']
        session_noun = 'session' if no_sessions == 1 else 'sessions'

        print(f"Processing {first_name}...")
        print(f"Email: {email}")
        print(f"Total Money: {total_money}")
        print(f"Number of Sessions: {no_sessions}\n")

        # Create the email body based on the number of sessions
        if no_sessions == 0:
            body = textwrap.dedent(f"""
                Hi {first_name}, 
                
                We hope you're doing well! We are sorry to have missed you at training in {month}.
                  
                Let us know if you have any questions and we hope to train with you soon!""")
        else:
            body = textwrap.dedent(f"""
            Hi {first_name}, 
            
            Thank you for training with us in {month}!

            You attended {int(no_sessions)} {session_noun}, totalling {total_money} euro.

            Please bring the total in cash at the next training session (preferably the exact amount for convenience).

            Thank you and see you at training👊""")
        
        # Append the email and body to the list
        email_data.append({'email': email, 'body': body})

can_write = input("Press Enter to save the emails to the Excel file...")
if can_write == "":
    # Convert to DataFrame
    email_df = pd.DataFrame(email_data, columns=['email', 'body'])

    # Save to a new sheet in the same Excel file
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
        email_df.to_excel(writer, sheet_name=f'00_{month}_emails', index=False)

    print("Emails generated and saved successfully! Check file for the output.")
    is_continue = input("Confirm to send emails? (Type 'Send' to continue)")
    if is_continue == "Send":
        # Send the emails
        for index, row in email_df.iterrows():
            receiver_email = row['email']
            body = row['body']
            send_email(receiver_email, subject, body)
    else:
        print("Quitting. Emails not sent yet.")