from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

# User roles
class User(AbstractUser):
    ROLE_CHOICES = [
        ('staff', 'Staff/Officer'),
        ('citizen', 'Citizen/User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    # Add any extra fields if needed





class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name
    




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
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
    resolved_details = models.TextField(null = True, help_text = "Enter the details of how issue was resolved")

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





