from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("You must provide a valid email address"))
        
    def create_user(self, first_name, last_name, email, password ,**extra_fields):
        if email:
             email = self.normalize_email(email)
             self.email_validator(email)    
        else:
            raise ValueError(_("You must provide an email address"))
        
        
        if not (first_name and last_name):
            raise ValidationError("You must submit a first name and last name")
        
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name, last_name, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True) 
        extra_fields.setdefault("is_superuser", True) 

        if extra_fields.get('is_staff') == False:
            raise ValidationError(_('Superuser must have is_staff = True'))
        if extra_fields.get('is_superuser') == False:
            raise ValidationError(_('Superuser must have is_superuser = True'))

        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            **extra_fields
        )

        return user
