from django.contrib import admin
from .models import User, Department, Complaint, ComplaintResponse, Feedback, Profile

admin.site.register(User)
admin.site.register(Department)
admin.site.register(Complaint)
admin.site.register(ComplaintResponse)
admin.site.register(Feedback)
admin.site.register(Profile)
