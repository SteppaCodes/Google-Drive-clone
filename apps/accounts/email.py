from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import threading
from rest_framework.exceptions import ValidationError
from .models import User


class EmailThread(threading.Thread):
    def __init__(self,email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send() 

class SendMail:

    @staticmethod
    def resetpassword(request, email, *args, **Kwargs):
        try:
            user = User.objects.get(email=email)
            subject = "Password Reset"
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            site_domain = get_current_site(request).domain
            #Url that calls our reset password view
            relative_url = reverse('reset-password-confirm', 
                                   kwargs={'uidb64':uidb64, 'token':token})
            #url that will be displayed in the email message
            abs_url = f"http://{site_domain}{relative_url}"

            message = EmailMessage(
                subject=subject,
                body= f"Hi {user.username}!, We received a request to reset your password\n Please click the link to reset\n {abs_url}\nIf you did not make this request, please ignore, someone might have entere your email by mistakae\nThank You!",
                to= [email]
            )
            message.content_subtype = "html"
            EmailThread(message).start()
        except User.DoesNotExist:
            raise ValidationError("user with email does not exist")