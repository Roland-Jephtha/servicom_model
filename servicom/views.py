from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
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

from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.core.mail import send_mail

from django.contrib.auth import login as auth_login
from django.utils.text import slugify
import uuid

User = get_user_model()



def home(request):
    return render(request, 'home/home.html')





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
                f"""
Dear {complaint.profile.user.first_name},

We have received your complaint and it has been successfully submitted to our system.

Your complaint reference number is: {complaint.reference}

Our team will review your submission and keep you updated on the progress. If you have any further questions, please reply to this email.

Best regards,
Servicom Service
""",
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
        return redirect('staff_dashboard')
    
    
    elif request.user.is_authenticated:
        # Citizen dashboard with their complaints
        profile = Profile.objects.get(user = request.user)

        user_complaints = Complaint.objects.filter(profile__user=request.user).order_by('-created_at')[:5]
        user_total = Complaint.objects.filter(profile__user=request.user).count()
        user_pending = Complaint.objects.filter(profile__user=request.user, status='pending').count()
        user_in_progress = Complaint.objects.filter(profile__user=request.user, status='in_progress').count()
        user_resolved = Complaint.objects.filter(profile__user=request.user, status='resolved').count()

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

# Staff views for managing complaints



@login_required
def staff_feedback_list(request):
    # Get feedbacks for complaints resolved by this staff member
    # We'll assume staff is associated with complaints through responses
    # staff_responses = Complaint.objects.filter(status='resolved')

    # Get all feedbacks for these complaints
    # feedbacks = Feedback.objects.filter(complaint__status='resolved').order_by('-created_at')
    staff_profile = Profile.objects.get(user=request.user)
    feedbacks = Feedback.objects.filter(complaint__department=staff_profile.department)

    # Calculate statistics
    total_feedback = feedbacks.count()
    average_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    positive_feedback = feedbacks.filter(rating__gte=4).count()
    negative_feedback = feedbacks.filter(rating__lte=2).count()

    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    context = {
        'feedbacks': feedbacks,
        'total_feedback': total_feedback,
        'average_rating': round(average_rating, 1),
        'positive_feedback': positive_feedback,
        'negative_feedback': negative_feedback,
        'staff_profile': staff_profile
    }
    return render(request, 'dashboard/staff_feedback.html', context)

def staff_dashboard(request):
    # Get complaint statistics for staff


    profile = Profile.objects.get(user = request.user)
    total_complaints = Complaint.objects.filter(department=profile.department).count()
    pending_complaints = Complaint.objects.filter(status='pending', department=profile.department).count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress', department=profile.department).count()
    resolved_complaints = Complaint.objects.filter(status='resolved', department=profile.department).count()

    # Calculate resolution rate
    resolution_rate = 0
    if total_complaints > 0:
        resolution_rate = (resolved_complaints / total_complaints) * 100

    # Calculate average wait time for pending complaints
    pending_complaints_with_dates = Complaint.objects.filter(status='pending', department=profile.department)
    if pending_complaints_with_dates.exists():
        avg_wait_time = 0
        for complaint in pending_complaints_with_dates:
            if complaint.created_at:
                days_waiting = (timezone.now() - complaint.created_at).days
                avg_wait_time += days_waiting
        avg_wait_time = avg_wait_time / pending_complaints_with_dates.count()
        avg_wait_time = f"{avg_wait_time:.1f} days"
    else:
        avg_wait_time = "N/A"

    # Calculate processing time for in-progress complaints
    in_progress_complaints_with_dates = Complaint.objects.filter(status='in_progress', department=profile.department)
    if in_progress_complaints_with_dates.exists():
        avg_processing_time = 0
        for complaint in in_progress_complaints_with_dates:
            if complaint.created_at:
                days_processing = (timezone.now() - complaint.created_at).days
                avg_processing_time += days_processing
        avg_processing_time = avg_processing_time / in_progress_complaints_with_dates.count()
        avg_processing_time = f"{avg_processing_time:.1f} days"
    else:
        avg_processing_time = "N/A"

    # Calculate monthly increase in resolved complaints

    # Get current month's resolved complaints
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = current_month + timedelta(days=32)
    next_month = next_month.replace(day=1)

    current_month_resolved = Complaint.objects.filter(
        status='resolved',
        updated_at__gte=current_month,
        updated_at__lt=next_month,
        department=profile.department
    ).count()

    # Get previous month's resolved complaints
    prev_month = current_month - timedelta(days=1)
    prev_month = prev_month.replace(day=1)
    two_months_ago = prev_month - timedelta(days=32)
    two_months_ago = two_months_ago.replace(day=1)

    prev_month_resolved = Complaint.objects.filter(
        status='resolved',
        updated_at__gte=prev_month,
        updated_at__lt=current_month,
        department=profile.department
    ).count()

    # Calculate percentage increase
    monthly_increase = "N/A"
    monthly_percentage = 0

    if prev_month_resolved > 0:
        increase = current_month_resolved - prev_month_resolved
        percentage = (increase / prev_month_resolved) * 100
        monthly_increase = f"{percentage:+.1f}%"
        monthly_percentage = min(100, max(0, percentage))  # Ensure percentage is between 0 and 100
    elif current_month_resolved > 0:
        monthly_increase = "+100%"
        monthly_percentage = 100

    # Get recent complaints
    recent_complaints = Complaint.objects.filter(department=profile.department).order_by('-created_at')[:5]

    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    # Get feedback for this staff member
    staff_responses = ComplaintResponse.objects.filter(responder=request.user, complaint__department=profile.department)
    resolved_complaints_for_staff = [response.complaint for response in staff_responses.filter(complaint__status='resolved')]
    staff_feedbacks = Feedback.objects.filter(complaint__in=resolved_complaints_for_staff).order_by('-created_at')
    feedback_count = staff_feedbacks.count()

    # Calculate feedback statistics
    average_rating = staff_feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    positive_feedback = staff_feedbacks.filter(rating__gte=4).count()
    negative_feedback = staff_feedbacks.filter(rating__lte=2).count()

    context = {
        'profile': profile,
        'recent_complaints': recent_complaints,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'staff_profile': staff_profile,
        'feedback_count': feedback_count,
        'staff_feedbacks': staff_feedbacks,
        'average_rating': round(average_rating, 1),
        'positive_feedback': positive_feedback,
        'negative_feedback': negative_feedback,
        # New calculated values
        'resolution_rate': round(resolution_rate, 1),
        'avg_wait_time': avg_wait_time,
        'avg_processing_time': avg_processing_time,
        'monthly_increase': monthly_increase,
        'monthly_percentage': monthly_percentage,
        'wait_time_percentage': min(100, max(0, (float(avg_wait_time.replace(' days', '')) / 7) * 100)) if avg_wait_time != "N/A" else 0,
        'processing_time_percentage': min(100, max(0, (float(avg_processing_time.replace(' days', '')) / 10) * 100)) if avg_processing_time != "N/A" else 0
    }
    return render(request, 'dashboard/staff_dashboard.html', context)
















def signup(request):
    if request.user.is_anonymous:
        if request.method == 'POST':
            fullname = request.POST.get('fullname', '').strip()
            email = request.POST.get('email', '').lower()
            password = request.POST.get('password')

            # ✅ Break fullname into first and last name
            parts = fullname.split()
            first_name = parts[0] if len(parts) > 0 else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

            # ✅ Generate unique username from fullname
            base_username = slugify(first_name + last_name)[:10]  # limit length
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Check if email already used
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already used')
                return redirect('signup')

            # ✅ Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create related profile
            profile = Profile(user=user)
            profile.save()

            # If custom User model has 'role' or 'position'
            if hasattr(user, "role"):
                user.role = 'citizen'
                user.save()

            # Send welcome email
            subject = 'Welcome to PTI Servicom'
            email_from = settings.EMAIL_HOST_USER
            message = f"""
                Dear {fullname},

                Thank you for registering with PTI Servicom. Your account has been successfully created and you can now log in to access our services.

                Please keep your account details secure and do not share them with anyone. If you have any questions or need assistance, feel free to contact us.

                Best regards,
                Servicom Service
                """
            try:
                send_mail("PTI Servicom", message, email_from, [email])
            except Exception as e:
                print(f"Email sending failed: {e}")  # Avoid breaking signup if email fails

            # Auto login user
            auth_login(request, user)

            messages.success(request, 'Account created successfully, you are now logged in.')
            return redirect('dashboard')
        else:
            return render(request, 'home/signup.html')
    else:
        return redirect("dashboard")



@login_required
def staff_view_complaint(request, reference):
    # Get the complaint
    staff_profile = Profile.objects.get(user=request.user)
    complaint = get_object_or_404(Complaint, reference=reference, department=staff_profile.department)

    # Get responses for this complaint
    responses = ComplaintResponse.objects.filter(complaint=complaint).order_by('created_at')

    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    context = {
        'complaint': complaint,
        'responses': responses,
        'staff_profile': staff_profile
    }
    return render(request, 'dashboard/staff_view_complaint.html', context)











@login_required
def staff_update_complaint_status(request, reference):
    # Get the complaint
    staff_profile = Profile.objects.get(user=request.user)
    complaint = get_object_or_404(Complaint, reference=reference, department=staff_profile.department)

    if request.method == 'POST':
        status = request.POST.get('status')
        resolved_details = request.POST.get('resolved_details', '')

        if status in dict(Complaint.STATUS_CHOICES):
            complaint.status = status
            if status == 'resolved':
                complaint.resolved_details = resolved_details
            complaint.save()

            # Add response if provided
            response_text = request.POST.get('response', '')
            if response_text:
                ComplaintResponse.objects.create(
                    complaint=complaint,
                    responder=request.user,
                    comment=response_text
                )

            # Send notification to user
            if complaint.profile and complaint.profile.user.email:
                send_mail(
                    'Complaint Status Update',
                    f"""
                        Dear {complaint.profile.user.first_name},

                        We would like to inform you that the status of your complaint (Reference: {complaint.reference}) has been updated to: {status}.

                        If you have any questions or require further assistance, please do not hesitate to contact us.

                        Best regards,
                        Servicom Service
                        """,
                    settings.DEFAULT_FROM_EMAIL,
                    [complaint.profile.user.email],
                    fail_silently=True,
                )

            messages.success(request, 'Complaint status updated successfully!')
            return redirect('staff_view_complaint', reference=reference)

    return redirect('staff_view_complaint', reference=reference)








@login_required
def staff_add_response(request, reference):
    # Get the complaint
    staff_profile = Profile.objects.get(user=request.user)
    complaint = get_object_or_404(Complaint, reference=reference, department=staff_profile.department)

    if request.method == 'POST':
        response_text = request.POST.get('response', '')

        if response_text:
            ComplaintResponse.objects.create(
                complaint=complaint,
                responder=request.user,
                comment=response_text
            )

            # Send notification to user
            if complaint.profile and complaint.profile.user.email:
                send_mail(
                    'New Response to Your Complaint',
                    f"""
                        Dear {complaint.profile.user.first_name},

                        A new response has been added to your complaint (Reference: {complaint.reference}).

                        Please log in to your Servicom dashboard to view the details and continue communication if needed.

                        Thank you for using our service.

                        Best regards,
                        Servicom Service
                        """,
                    settings.DEFAULT_FROM_EMAIL,
                    [complaint.profile.user.email],
                    fail_silently=True,
                )

            messages.success(request, 'Response added successfully!')
            return redirect('staff_view_complaint', reference=reference)

    return redirect('staff_view_complaint', reference=reference)











@login_required
def staff_view_all_complaints(request):
    # Get all complaints
    staff_profile = Profile.objects.get(user=request.user)
    complaints = Complaint.objects.filter(department=staff_profile.department).order_by('-created_at')

    # Get statistics
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()

    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    context = {
        'complaints': complaints,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'staff_profile': staff_profile
    }
    return render(request, 'dashboard/staff_view_all_complaints.html', context)








@login_required
def staff_profile_view(request):
    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    context = {
        'staff_profile': staff_profile
    }
    return render(request, 'dashboard/staff_profile.html', context)










@login_required
def staff_edit_profile(request):
    # Get staff profile
    staff_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=staff_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('staff_profile_view')
        else:
            # Loop through form errors and add them to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserProfileForm(instance=staff_profile)

    context = {
        'staff_profile': staff_profile,
        'form': form
    }
    return render(request, 'dashboard/staff_edit_profile.html', context)










# Helper function to check if user is staff
def is_staff(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'staff'





















def login(request):
    if request.user.is_anonymous:
        if request.method == "POST":
            email = request.POST["email"].lower()
            password = request.POST["password"]
            user = authenticate(email=email, password=password)
            if user is not None:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                messages.success(request, "Login successful!")
                return redirect("dashboard")

            else:
                messages.error(request, "Invalid email or password")
                return redirect('login')
    else:
        return redirect("dashboard")
    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')