from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver




# User roles
class User(AbstractUser):
    ROLE_CHOICES = [
        ('staff', 'Staff/Officer'),
        ('citizen', 'Citizen/User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    # Add any extra fields if needed
    email = models.EmailField(unique=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']










class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name
    




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    mat_no = models.CharField(max_length=30, blank=True, null = True)
    address = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    bio = models.TextField(null = True)
    profile_image = models.ImageField(upload_to = 'profile-image', null = True, blank = True)
    def __str__(self):
        return self.user.username






class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    TYPE_CHOICES = [
        ('services', 'Services'),
        ('goods', 'Goods'),

    ]
    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=100, choices = TYPE_CHOICES, null = True)
    description = models.TextField()
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file = models.FileField(upload_to='complaints/', blank=True, null=True)
    resolved_details = models.TextField(null = True, help_text = "Enter the details of how issue was resolved", blank = True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.reference} - {self.department}"





class ComplaintResponse(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"Response to {self.complaint.reference} by {self.responder}"






class Feedback(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"Feedback for {self.complaint.reference}"




from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# Store old is_active state before saving
@receiver(pre_save, sender=User)
def store_old_is_active(sender, instance, **kwargs):
    if instance.pk:  # existing user
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_is_active = old_instance.is_active
        except sender.DoesNotExist:
            instance._old_is_active = instance.is_active
    else:
        instance._old_is_active = instance.is_active


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # Ensure profile exists
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()

    # Only send if existing user got activated
    if not created:
        old_is_active = getattr(instance, "_old_is_active", None)
        if old_is_active is False and instance.is_active is True:
            subject = 'Your PTI Servicom Account is Now Active'
            message = f"""
Dear {instance.get_full_name() or instance.username},

Your account has been approved and activated by the administrator. You can now log in and access all services.

Best regards,
Servicom Service
"""
            email_from = settings.EMAIL_HOST_USER
            send_mail(subject, message, email_from, [instance.email], fail_silently=True)
