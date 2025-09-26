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
        
        # Create verification link that points directly to your API
        verification_link = f"https://api.cycle.co.ke/auth/verify-email?token={user_id}"
        
        # HTML email with styled button
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ background: #667eea; color: white; padding: 15px 30px; 
                         text-decoration: none; border-radius: 25px; display: inline-block; 
                         margin: 20px 0; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Cycle!</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Thank you for signing up for Cycle! Please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
                    
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create this account, please ignore this email.</p>
                    
                    <p>Best regards,<br/>The Cycle Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Cycle. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
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

def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email to user"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.email_from
        msg['To'] = email
        msg['Subject'] = "Reset your Cycle password"
        
        # Create reset link that points directly to your API
        reset_url = f"https://api.cycle.co.ke/auth/reset-password?token={reset_token}"
        
        # HTML email with styled button
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
                         padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ background: #ff6b6b; color: white; padding: 15px 30px; 
                         text-decoration: none; border-radius: 25px; display: inline-block; 
                         margin: 20px 0; font-weight: bold; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; 
                          border-radius: 5px; margin: 20px 0; color: #856404; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>You requested to reset your password for your Cycle account.</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This link will expire in 1 hour.
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #ff6b6b;">{reset_url}</p>
                    
                    <p>If you didn't request this password reset, please ignore this email.<br>
                    Your account remains secure.</p>
                    
                    <p>Best regards,<br/>The Cycle Team</p>
                </div>
                <div class="footer">
                    <p>© 2025 Cycle. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.email_from, email, text)
        server.quit()
        
        print(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False