"""
Email service — sends branded HTML emails for Shadow.
Uses SMTP when configured, logs to console in dev mode.
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from html import escape

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@shadow.pau.edu.ng")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------
_NAVY = "#1e3a8a"
_NAVY_DARK = "#172554"
_NAVY_DARKEST = "#0f1a3e"
_GOLD = "#f5b731"
_SURFACE = "#f8f9fb"
_WHITE = "#ffffff"
_TEXT = "#1a1d2b"
_TEXT_MUTED = "#9ba2b5"
_SUCCESS = "#059669"
_WARNING = "#D97706"
_ERROR = "#DC2626"
_FONT_BODY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
_FONT_DISPLAY = "Georgia, 'Times New Roman', serif"


# ---------------------------------------------------------------------------
# SMTP helpers (preserved)
# ---------------------------------------------------------------------------
def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP in a background thread (never blocks the request)."""
    if not _smtp_configured():
        logger.info(
            "SMTP not configured — email would be sent:\n"
            "  To: %s\n  Subject: %s",
            to, subject,
        )
        return True

    import threading

    def _do_send():
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = to
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, to, msg.as_string())

            logger.info("Email sent to %s: %s", to, subject)
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, e)

    threading.Thread(target=_do_send, daemon=True).start()
    return True


# ---------------------------------------------------------------------------
# Base template builder
# ---------------------------------------------------------------------------
def _build_email(
    subject: str,
    heading: str,
    body_html: str,
    cta_text: str,
    cta_url: str,
    accent_color: str = _GOLD,
) -> str:
    """Build a complete branded HTML email.

    Parameters
    ----------
    subject : str
        Used in the <title> tag.
    heading : str
        Display heading rendered above the body content.
    body_html : str
        Inner HTML placed inside the white content card.
    cta_text : str
        Label for the primary call-to-action button.
    cta_url : str
        Destination URL for the CTA button.
    accent_color : str, optional
        The thin accent line colour between header and body.
        Defaults to gold; pass ``_ERROR`` for critical alerts.
    """
    # Escape URL and CTA text to prevent XSS injection
    safe_cta_url = escape(cta_url, quote=True)
    safe_cta_text = escape(cta_text)

    return f"""\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(subject)}</title>
  <!--[if mso]>
  <style type="text/css">
    body, table, td {{ font-family: Arial, sans-serif !important; }}
  </style>
  <![endif]-->
</head>
<body style="margin:0; padding:0; background-color:{_SURFACE}; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;">

  <!-- Outer wrapper -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:{_SURFACE};">
    <tr>
      <td align="center" style="padding: 24px 16px 40px 16px;">

        <!-- Container 560px -->
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" border="0"
               style="max-width:560px; width:100%;">

          <!-- ============ HEADER ============ -->
          <tr>
            <td style="background-color:{_NAVY_DARKEST}; border-radius:12px 12px 0 0; padding:16px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="vertical-align:middle;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <!-- S logo square -->
                        <td style="vertical-align:middle; padding-right:10px;">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td style="background-color:{_NAVY}; border-radius:6px; width:30px; height:30px;
                                         text-align:center; vertical-align:middle;
                                         font-family:{_FONT_DISPLAY}; font-size:17px;
                                         font-weight:bold; color:{_GOLD}; line-height:30px;">
                                S
                              </td>
                            </tr>
                          </table>
                        </td>
                        <!-- Shadow wordmark -->
                        <td style="vertical-align:middle; font-family:{_FONT_DISPLAY};
                                   font-size:18px; font-weight:bold; color:{_WHITE};
                                   letter-spacing:0.5px;">
                          Shadow
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ============ GOLD ACCENT LINE ============ -->
          <tr>
            <td style="height:2px; background-color:{accent_color}; font-size:1px; line-height:1px;">
              &nbsp;
            </td>
          </tr>

          <!-- ============ BODY CARD ============ -->
          <tr>
            <td style="background-color:{_WHITE}; padding:36px 36px 12px 36px;">

              <!-- Heading -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="font-family:{_FONT_DISPLAY}; font-size:22px; font-weight:bold;
                             color:{_TEXT}; padding-bottom:20px; line-height:1.3;">
                    {heading}
                  </td>
                </tr>
              </table>

              <!-- Body content -->
              {body_html}

            </td>
          </tr>

          <!-- ============ CTA SECTION ============ -->
          <tr>
            <td style="background-color:{_WHITE}; padding:8px 36px 36px 36px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="border-radius:8px; background-color:{_NAVY};">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
                                 xmlns:w="urn:schemas-microsoft-com:office:word"
                                 href="{safe_cta_url}" style="height:42px;v-text-anchor:middle;width:200px;"
                                 arcsize="19%" strokecolor="{_NAVY}" fillcolor="{_NAVY}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:14px;font-weight:bold;">
                        {safe_cta_text}
                      </center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{safe_cta_url}"
                       target="_blank"
                       style="display:inline-block; background-color:{_NAVY}; color:{_WHITE};
                              font-family:{_FONT_BODY}; font-size:14px; font-weight:600;
                              text-decoration:none; padding:12px 32px; border-radius:8px;
                              line-height:1.4;">
                      {safe_cta_text}
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ============ FOOTER ============ -->
          <tr>
            <td style="background-color:{_SURFACE}; border-top:1px solid #e5e7eb;
                       border-radius:0 0 12px 12px; padding:24px 36px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="font-family:{_FONT_BODY}; font-size:12px; color:{_TEXT_MUTED};
                             line-height:1.6; text-align:center;">
                    Shadow &mdash; Pan-Atlantic University<br/>
                    This is an automated message. Please do not reply directly.<br/>
                    You&#8217;re receiving this because you have a Shadow account.
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
        <!-- /Container -->

      </td>
    </tr>
  </table>
  <!-- /Outer wrapper -->

</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers for body fragments
# ---------------------------------------------------------------------------
def _p(text: str, extra_style: str = "") -> str:
    """Render a paragraph with standard styling."""
    style = (
        f"font-family:{_FONT_BODY}; font-size:15px; color:{_TEXT}; "
        f"line-height:1.65; margin:0 0 16px 0; {extra_style}"
    )
    return f'<p style="{style}">{text}</p>'


def _small(text: str, extra_style: str = "") -> str:
    """Render small muted text."""
    style = (
        f"font-family:{_FONT_BODY}; font-size:13px; color:{_TEXT_MUTED}; "
        f"line-height:1.5; margin:0 0 12px 0; {extra_style}"
    )
    return f'<p style="{style}">{text}</p>'


def _detail_row(label: str, value: str) -> str:
    """Render a label-value row inside a table."""
    return f"""\
<tr>
  <td style="font-family:{_FONT_BODY}; font-size:13px; color:{_TEXT_MUTED};
             padding:6px 12px 6px 0; vertical-align:top; white-space:nowrap;">
    {escape(label)}
  </td>
  <td style="font-family:{_FONT_BODY}; font-size:14px; color:{_TEXT};
             font-weight:600; padding:6px 0; vertical-align:top;">
    {escape(value)}
  </td>
</tr>"""


def _detail_table(rows_html: str, border_left_color: str = "") -> str:
    """Wrap detail rows in a styled table, optionally with a left border accent."""
    border_style = (
        f"border-left:3px solid {border_left_color}; padding-left:16px;"
        if border_left_color else ""
    )
    return f"""\
<table role="presentation" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 20px 0; {border_style}">
  {rows_html}
</table>"""


# ---------------------------------------------------------------------------
# 1. Verification / Welcome email
# ---------------------------------------------------------------------------
def send_verification_email(to: str, token: str, name: str) -> bool:
    """Send a welcome email with a verification link."""
    safe_name = escape(name)
    verify_url = f"{FRONTEND_URL}/verify-email/{token}"
    subject = "Welcome to Shadow \u2014 Verify your email"

    body_html = (
        _p(f"Hi {safe_name},")
        + _p(
            "Welcome to Shadow! We help Pan-Atlantic University students "
            "reach their target CGPA through intelligent planning, grade predictions, "
            "and AI-powered study recommendations."
        )
        + _p(
            "Please verify your email address to unlock the full Shadow experience. "
            "Just tap the button below."
        )
    )

    # Append expiry note below the CTA (it will sit in the body card above CTA)
    body_html += _small("This verification link expires in 24 hours.")

    html = _build_email(
        subject=subject,
        heading="Verify your email",
        body_html=body_html,
        cta_text="Verify Email",
        cta_url=verify_url,
    )
    return _send_email(to, subject, html)


# ---------------------------------------------------------------------------
# 2. Password reset email
# ---------------------------------------------------------------------------
def send_password_reset_email(to: str, token: str, name: str) -> bool:
    """Send a password reset email with a secure link."""
    safe_name = escape(name)
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "Shadow \u2014 Reset your password"

    body_html = (
        _p(f"Hi {safe_name},")
        + _p(
            "We received a request to reset the password on your Shadow account. "
            "Click the button below to choose a new password."
        )
        + _small("This link expires in 1 hour.")
        + _small(
            "If you didn&#8217;t request this, no action is needed &mdash; "
            "your account is safe.",
            extra_style=f"color:{_TEXT_MUTED}; font-style:italic;",
        )
    )

    html = _build_email(
        subject=subject,
        heading="Reset your password",
        body_html=body_html,
        cta_text="Reset Password",
        cta_url=reset_url,
    )
    return _send_email(to, subject, html)


# ---------------------------------------------------------------------------
# 3. Task overdue email (CRITICAL)
# ---------------------------------------------------------------------------
def send_task_overdue_email(
    to: str,
    name: str,
    task_title: str,
    course_name: str,
    due_date: str,
) -> bool:
    """Send an urgent notification that a task is overdue."""
    safe_name = escape(name)
    subject = f"Shadow Alert \u2014 Overdue task: {task_title}"
    dashboard_url = f"{FRONTEND_URL}/dashboard"

    # Alert icon (HTML-rendered warning triangle)
    alert_icon = (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:0 0 16px 0;">'
        f"<tr>"
        f'<td style="background-color:#FEF2F2; border-radius:50%; width:40px; height:40px; '
        f"text-align:center; vertical-align:middle; font-size:20px; line-height:40px;\">"
        f"&#9888;"
        f"</td>"
        f"</tr>"
        f"</table>"
    )

    detail_rows = (
        _detail_row("Task", task_title)
        + _detail_row("Course", course_name)
        + _detail_row("Due date", due_date)
    )

    body_html = (
        alert_icon
        + _p(f"Hi {safe_name},")
        + _p(
            "A task on your schedule has passed its due date. "
            "Staying on track is important for hitting your CGPA target "
            "&mdash; take a moment to review and reschedule if needed."
        )
        + _detail_table(detail_rows, border_left_color=_ERROR)
        + _small(
            "Tip: Break large tasks into smaller steps and set realistic deadlines."
        )
    )

    html = _build_email(
        subject=subject,
        heading="Task overdue",
        body_html=body_html,
        cta_text="View Tasks",
        cta_url=dashboard_url,
        accent_color=_ERROR,
    )
    return _send_email(to, subject, html)


# ---------------------------------------------------------------------------
# 4. CGPA alert email (CRITICAL)
# ---------------------------------------------------------------------------
def send_cgpa_alert_email(
    to: str,
    name: str,
    current_cgpa: float,
    target_cgpa: float,
    classification: str,
) -> bool:
    """Send a CGPA status update with visual progress bar."""
    safe_name = escape(name)
    safe_class = escape(classification)
    subject = f"Shadow \u2014 CGPA Update: {current_cgpa:.2f}"
    cgpa_url = f"{FRONTEND_URL}/cgpa"

    # Calculate progress as a percentage of 5.0 scale
    current_pct = min(max(int((current_cgpa / 5.0) * 100), 0), 100)
    target_pct = min(max(int((target_cgpa / 5.0) * 100), 0), 100)

    # Determine bar colour based on how close current is to target
    if current_cgpa >= target_cgpa:
        bar_color = _SUCCESS
    elif current_cgpa >= target_cgpa - 0.3:
        bar_color = _WARNING
    else:
        bar_color = _ERROR

    # Visual progress bar (table-based for email compatibility)
    progress_bar = f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 6px 0;">
  <tr>
    <td style="font-family:{_FONT_BODY}; font-size:13px; color:{_TEXT_MUTED};">
      Current
    </td>
    <td align="right" style="font-family:{_FONT_BODY}; font-size:13px; color:{_TEXT_MUTED};">
      Target: {target_cgpa:.2f}
    </td>
  </tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 4px 0;">
  <tr>
    <td style="background-color:#e5e7eb; border-radius:4px; padding:0; height:10px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"
             style="width:{current_pct}%; max-width:100%;">
        <tr>
          <td style="background-color:{bar_color}; border-radius:4px; height:10px;
                     font-size:1px; line-height:1px;">
            &nbsp;
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 20px 0;">
  <tr>
    <td style="font-family:{_FONT_BODY}; font-size:22px; font-weight:bold; color:{_TEXT};">
      {current_cgpa:.2f}
      <span style="font-size:13px; font-weight:normal; color:{_TEXT_MUTED};">/ 5.00</span>
    </td>
    <td align="right" style="font-family:{_FONT_BODY}; font-size:13px; color:{_TEXT};
                              vertical-align:bottom; padding-bottom:4px;">
      {safe_class}
    </td>
  </tr>
</table>"""

    # Target marker (thin line on the track)
    # We embed a subtle marker inside the bar section above via the target label

    # Choose encouraging tone
    if current_cgpa >= target_cgpa:
        encouragement = (
            "You&#8217;re on track or above your target &mdash; fantastic work! "
            "Keep the momentum going."
        )
    elif current_cgpa >= target_cgpa - 0.3:
        encouragement = (
            "You&#8217;re close to your target. A strong finish this semester "
            "can make all the difference &mdash; you&#8217;ve got this."
        )
    else:
        encouragement = (
            "There&#8217;s a gap between your current CGPA and your target, but "
            "there&#8217;s still time to close it. Focus on high-credit courses and "
            "use your study plans to stay consistent."
        )

    body_html = (
        _p(f"Hi {safe_name},")
        + _p("Here&#8217;s your latest CGPA snapshot:")
        + progress_bar
        + _p(encouragement)
        + _small(
            "Visit your analytics page for a detailed breakdown by semester."
        )
    )

    html = _build_email(
        subject=subject,
        heading="CGPA update",
        body_html=body_html,
        cta_text="View Analytics",
        cta_url=cgpa_url,
        accent_color=bar_color,
    )
    return _send_email(to, subject, html)


# ---------------------------------------------------------------------------
# 5. Study plan complete email
# ---------------------------------------------------------------------------
def send_study_plan_complete_email(
    to: str,
    name: str,
    plan_topic: str,
    days_completed: int,
    total_days: int,
) -> bool:
    """Send a celebratory email when a study plan is completed."""
    safe_name = escape(name)
    safe_topic = escape(plan_topic)
    subject = f"Shadow \u2014 Study plan complete: {plan_topic}"
    smartstudy_url = f"{FRONTEND_URL}/smartstudy"

    # Completion badge / checkmark circle
    badge = (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="margin:0 auto 20px auto;">'
        f"<tr>"
        f'<td align="center" style="background-color:#ECFDF5; border-radius:50%; '
        f"width:52px; height:52px; text-align:center; vertical-align:middle; "
        f'font-size:26px; line-height:52px; color:{_SUCCESS};">'
        f"&#10003;"
        f"</td>"
        f"</tr>"
        f"</table>"
    )

    # Stats
    completion_pct = (
        int((days_completed / total_days) * 100) if total_days > 0 else 100
    )

    stats_html = f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="margin:0 0 20px 0; background-color:{_SURFACE}; border-radius:8px;">
  <tr>
    <td align="center" style="padding:16px 12px; border-right:1px solid #e5e7eb;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td align="center" style="font-family:{_FONT_BODY}; font-size:22px;
                                     font-weight:bold; color:{_TEXT}; line-height:1.2;">
            {days_completed}/{total_days}
          </td>
        </tr>
        <tr>
          <td align="center" style="font-family:{_FONT_BODY}; font-size:12px;
                                     color:{_TEXT_MUTED}; padding-top:4px;">
            Days completed
          </td>
        </tr>
      </table>
    </td>
    <td align="center" style="padding:16px 12px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td align="center" style="font-family:{_FONT_BODY}; font-size:22px;
                                     font-weight:bold; color:{_SUCCESS}; line-height:1.2;">
            {completion_pct}%
          </td>
        </tr>
        <tr>
          <td align="center" style="font-family:{_FONT_BODY}; font-size:12px;
                                     color:{_TEXT_MUTED}; padding-top:4px;">
            Completion rate
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>"""

    body_html = (
        badge
        + _p(
            f"Hi {safe_name},",
            extra_style="text-align:center;",
        )
        + _p(
            f"You&#8217;ve completed your study plan for "
            f"<strong>{safe_topic}</strong>. That&#8217;s a real achievement "
            f"&mdash; consistency is the key to academic success.",
            extra_style="text-align:center;",
        )
        + stats_html
        + _p(
            "Ready for the next challenge? Head to SmartStudy to generate "
            "a new plan or explore additional resources.",
            extra_style="text-align:center;",
        )
    )

    html = _build_email(
        subject=subject,
        heading="Study plan complete!",
        body_html=body_html,
        cta_text="View Study Plans",
        cta_url=smartstudy_url,
        accent_color=_SUCCESS,
    )
    return _send_email(to, subject, html)
