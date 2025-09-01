from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Complaint, Department, ComplaintResponse, Feedback, Profile
from .forms import (
    ComplaintForm,
    FeedbackForm,
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserProfileForm
)
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()



def home(request):
    return render(request, 'dashboard/home.html')





def charter(request):
    return render(request, 'dashboard/charter.html')




def submit_complaint(request):
    if request.method == 'POST':
        profile = Profile.objects.get(user = request.user)
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            if request.user.is_authenticated:
                complaint.profile = profile
            complaint.save()
            # Send notification (simplified)
            send_mail(
                'Complaint Submitted',
                f'Your complaint has been submitted. Reference: {complaint.reference}',
                settings.DEFAULT_FROM_EMAIL,
                [complaint.profile.user.email] if complaint.profile.user.email else [],
                fail_silently=True,
            )
            messages.success(request, 'Complaint submitted successfully!')
            return redirect('track_complaint', reference=complaint.reference)
    else:
        form = ComplaintForm()
    return render(request, 'dashboard/submit_complaint.html', {'form': form})



# def track_complaint(request, reference):
#     complaint = get_object_or_404(Complaint, reference=reference)
#     feedback_given = hasattr(complaint, 'feedback')
#     return render(request, 'dashboard/track_complaint.html', {'complaint': complaint, 'feedback_given': feedback_given})







@login_required
def track_complaint(request, reference):
    profile = get_object_or_404(Profile, user=request.user)
    complaint = get_object_or_404(Complaint, reference=reference, profile=profile)
    feedback_given = hasattr(complaint, 'feedback')

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.complaint = complaint
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('track_complaint', reference=reference)
    else:
        form = FeedbackForm()

    return render(request, 'dashboard/track_complaint.html', {
        'complaint': complaint,
        'feedback_given': feedback_given,
        'form': form
    })


@login_required
def give_feedback(request, reference):
    profile = get_object_or_404(Profile, user = request.user)
    complaint = get_object_or_404(Complaint, reference=reference, profile=profile)
    if hasattr(complaint, 'feedback'):
        messages.info(request, 'Feedback already submitted.')
        return redirect('track_complaint', reference=reference)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.complaint = complaint
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('track_complaint', reference=reference)
    else:
        form = FeedbackForm()
    return render(request, 'dashboard/send_feedback.html', {'form': form, 'complaint': complaint})





# Authentication Views
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')



        

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')




class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'auth/sign-up.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! Please log in.')
        return response
    




def dashboard(request):
    # Get complaint statistics for all users
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    recent_complaints = Complaint.objects.all().order_by('-created_at')[:5]

    # Check if user is authenticated and has role attribute
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'staff':
        # Staff dashboard with complaint management
        context = {
            'recent_complaints': recent_complaints,
            'total_complaints': total_complaints,
            'pending_complaints': pending_complaints,
            'in_progress_complaints': in_progress_complaints,
            'resolved_complaints': resolved_complaints,
        }
        return render(request, 'admin/dashboard.html', context)
    
    
    elif request.user.is_authenticated:
        # Citizen dashboard with their complaints
        profile = Profile.objects.get(user = request.user)

        user_complaints = Complaint.objects.filter(profile=profile).order_by('-created_at')[:5]
        user_total = Complaint.objects.filter(profile=profile).count()
        user_pending = Complaint.objects.filter(profile=profile, status='pending').count()
        user_in_progress = Complaint.objects.filter(profile=profile, status='in_progress').count()
        user_resolved = Complaint.objects.filter(profile=profile, status='resolved').count()

        context = {
            'user_complaints': user_complaints,
            'total_complaints': user_total,
            'pending_complaints': user_pending,
            'in_progress_complaints': user_in_progress,
            'resolved_complaints': user_resolved,
        }
        return render(request, 'dashboard/dashboard_user.html', context)
    else:
        # Anonymous user - show general dashboard
        context = {
            'recent_complaints': recent_complaints,
            'total_complaints': total_complaints,
            'pending_complaints': pending_complaints,
            'in_progress_complaints': in_progress_complaints,
            'resolved_complaints': resolved_complaints,
        }
        return render(request, 'dashboard/dashboard.html', context)

@login_required
def profile_view(request):
    return render(request, 'dashboard/profile.html', {'user': request.user})




@login_required
def edit_profile(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)  # ✅ use profile, not request.user
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user  # just to be safe
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('edit_profile')
        else:
            # Loop through form errors and add them to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserProfileForm(instance=profile)  # ✅ use profile, not request.user

    context = {
        'profile': profile,
        'form': form
    }
    return render(request, 'dashboard/profile.html', context)



@login_required
def my_complaints(request):
    # user_complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    profile = Profile.objects.get(user = request.user)
    user_complaints = Complaint.objects.filter(profile=profile).order_by('-created_at')
    context = {
        'user_complaints': user_complaints
    }
    return render(request, 'dashboard/my_complaints.html', context)


@login_required
def complaints_list(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()

    context = {
        'complaints': complaints,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
    }
    return render(request, 'dashboard/complaints.html', context)




@login_required
def feedback_list(request):
    feedback_list = Feedback.objects.all().order_by('-created_at')
    total_feedback = Feedback.objects.count()

    # Calculate average rating
    from django.db.models import Avg
    average_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg'] or 0

    positive_feedback = Feedback.objects.filter(rating__gte=4).count()
    negative_feedback = Feedback.objects.filter(rating__lte=2).count()

    context = {
        'feedback_list': feedback_list,
        'total_feedback': total_feedback,
        'average_rating': round(average_rating, 1),
        'positive_feedback': positive_feedback,
        'negative_feedback': negative_feedback,
    }
    return render(request, 'dashboard/feedback.html', context)

# Admin/dashboard/Staff views for managing complaints would go here
# ...
