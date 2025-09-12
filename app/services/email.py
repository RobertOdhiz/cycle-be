import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def send_verification_email(email: str, user_id: str) -> bool:
    """Send verification email to user"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.email_from
        msg['To'] = email
        msg['Subject'] = "Verify your Cycle account"
        
        # Create verification link
        verification_link = f"https://cycle.com/verify-email?token={user_id}"
        
        # Email body
        body = f"""
        Welcome to Cycle!
        
        Please verify your email address by clicking the link below:
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        The Cycle Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.email_from, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
