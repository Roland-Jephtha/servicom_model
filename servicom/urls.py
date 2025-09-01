from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('charter/', views.charter, name='charter'),

    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Dashboard and Profile URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Complaint URLs
    path('complaint/submit/', views.submit_complaint, name='submit_complaint'),
    path('complaint/track/<uuid:reference>/', views.track_complaint, name='track_complaint'),
    path('complaint/feedback/<uuid:reference>/', views.give_feedback, name='give_feedback'),
    path('complaints/', views.complaints_list, name='complaints_list'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('feedback/', views.feedback_list, name='feedback_list'),

    # Add more paths for admin/staff/servicom actions as needed
]
