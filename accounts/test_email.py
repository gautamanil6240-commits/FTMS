from django.core.mail import send_mail

send_mail(
    'FTMS Test',
    'SMTP Working Successfully',
    'YOUR_GMAIL@gmail.com',
    ['YOUR_GMAIL@gmail.com'],
    fail_silently=False,
)

print("Email Sent")