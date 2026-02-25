from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

fm = FastMail(mail_config)


async def send_otp_email(
    email_to: str,
    otp: str,
    subject: str = "Your TaskSphere OTP",
    heading: str = "TaskSphere",
    body_line: str = "Use the OTP below:",
) -> None:
    """Send a styled HTML OTP email. Used for register, login, and password reset."""
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 24px; background: #f9f9f9;">
        <div style="max-width:480px; margin:auto; background:#fff; border-radius:10px; padding:32px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <h2 style="color:#4F46E5; margin-top:0;">{heading}</h2>
          <p style="color:#444;">{body_line}</p>
          <div style="
            display:inline-block;
            padding: 14px 32px;
            background:#4F46E5;
            color:#fff;
            font-size:34px;
            letter-spacing:10px;
            border-radius:8px;
            margin: 16px 0;
            font-weight:bold;
          ">
            {otp}
          </div>
          <p style="color:#444;">This OTP is valid for <strong>5 minutes</strong>.</p>
          <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
          <p style="color:#aaa; font-size:12px;">
            If you didn't request this, you can safely ignore this email.
          </p>
        </div>
      </body>
    </html>
    """
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=MessageType.html,
    )
    await fm.send_message(message)


async def send_invite_email(
    email_to: str,
    name: str,
    temp_password: str,
    role: str,
    invited_by: str,
) -> None:
    """Send a welcome email to a newly invited user with their temp credentials."""
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 24px; background: #f9f9f9;">
        <div style="max-width:480px; margin:auto; background:#fff; border-radius:10px; padding:32px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <h2 style="color:#4F46E5; margin-top:0;">You've been invited to TaskSphere!</h2>
          <p style="color:#444;">Hi <strong>{name}</strong>,</p>
          <p style="color:#444;">
            <strong>{invited_by}</strong> has invited you to join their workspace as a <strong>{role.capitalize()}</strong>.
          </p>
          <p style="color:#444;">Here are your login credentials:</p>
          <table style="width:100%; border-collapse:collapse; margin:16px 0;">
            <tr>
              <td style="padding:8px 12px; background:#f3f4f6; border-radius:4px 0 0 4px; color:#555; font-weight:bold; width:40%;">Email</td>
              <td style="padding:8px 12px; background:#f3f4f6; border-radius:0 4px 4px 0; color:#222;">{email_to}</td>
            </tr>
            <tr><td colspan="2" style="padding:4px;"></td></tr>
            <tr>
              <td style="padding:8px 12px; background:#f3f4f6; border-radius:4px 0 0 4px; color:#555; font-weight:bold;">Temp Password</td>
              <td style="padding:8px 12px; background:#f3f4f6; border-radius:0 4px 4px 0; color:#222; font-family:monospace; letter-spacing:2px;">{temp_password}</td>
            </tr>
          </table>
          <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
          <p style="color:#aaa; font-size:12px;">If you weren't expecting this invitation, you can safely ignore this email.</p>
        </div>
      </body>
    </html>
    """
    message = MessageSchema(
        subject="You're invited to TaskSphere",
        recipients=[email_to],
        body=body,
        subtype=MessageType.html,
    )
    await fm.send_message(message)

