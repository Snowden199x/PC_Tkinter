"""
email_templates.py
Pure-Python email templates — mirrors the HTML files in web_development.
Each function returns a complete HTML string ready to send.
"""


def reset_password_email(
    org_name: str,
    reset_link: str,
    to_email: str,
    requested_at: str,
    banner_url: str = "",
) -> str:
    """
    Mirrors web_development/pres_view/templates/pres/email_reset_password.html
    Returns the full HTML body for the password-reset email.
    """
    banner_img = (
        f'<img src="{banner_url}" alt="PockiTrack Banner" '
        'style="max-width:100%;height:auto;display:block;margin:0 auto 16px auto;" />'
        if banner_url else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>PockiTrack – Reset Password</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background: #f7f7f7;
      margin: 0;
      padding: 0;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 0 auto;
      background: #ffffff;
      padding: 20px;
    }}
    .banner {{
      text-align: center;
      padding: 10px 0 20px 0;
      border-bottom: 1px solid #eee;
    }}
    .btn {{
      display: inline-block;
      margin-top: 20px;
      padding: 10px 20px;
      background: #f4a025;
      color: #ffffff !important;
      text-decoration: none;
      border-radius: 4px;
      font-weight: bold;
    }}
    p {{
      color: #333333;
      line-height: 1.5;
    }}
    .system-box, .contact-box {{
      margin-top: 24px;
      padding: 12px 16px;
      background: #f3f3f3;
      border-radius: 12px;
      font-size: 12px;
    }}
    .footer {{
      margin-top: 20px;
      padding: 10px 16px;
      background: #f4a025;
      color: #ffffff;
      font-size: 11px;
      text-align: center;
      border-radius: 12px;
    }}
    .footer a {{ color: #ffffff; text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="banner">
      {banner_img}
    </div>

    <p>Hi {org_name},</p>

    <p>
      You requested to reset your password for your PockiTrack organization account.
    </p>
    <p>Click the button below to reset your password:</p>

    <p style="text-align:center;">
      <a href="{reset_link}" class="btn">Reset your password</a>
    </p>

    <p>If the button does not work, copy and paste this link into your browser:</p>
    <p>{reset_link}</p>

    <p>If you did not request this, you can ignore this email.</p>
    <p>Regards,<br />PockiTrack Team</p>

    <div class="system-box">
      <p>This is a system generated message. Do not reply.</p>
      <p>
        This message is intended to {to_email} upon request this {requested_at}.
      </p>
    </div>

    <div class="contact-box">
      <p>
        If you have questions, feedback or suggestions, feel free to contact us at
        <a href="mailto:pockitrack2k25@gmail.com">pockitrack2k25@gmail.com</a>.
      </p>
    </div>

    <div class="footer">&copy; 2025 PockiTrack. All rights reserved.</div>
  </div>
</body>
</html>"""
