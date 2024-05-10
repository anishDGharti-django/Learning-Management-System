import random
from django.template.loader import render_to_string

from  django.core.mail import EmailMessage
from django.conf import settings

def createOtp():
    otp = random.randint(10000, 99999)
    return otp




def sendMail(user, mail_subject, email_template, link):
    from_email = settings.DEFAULT_FROM_EMAIL
    print("i am here")
    message = render_to_string(email_template, {
        'user': user,
        'link': link,
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    # mail.content_subtype = 'html'
    mail.send()


