from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('charter/', views.charter, name='charter'),

    # Authentication URLs
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),

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

    # Staff URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/complaints/', views.staff_view_all_complaints, name='staff_view_all_complaints'),
    path('staff/complaint/<uuid:reference>/', views.staff_view_complaint, name='staff_view_complaint'),
    path('staff/complaint/<uuid:reference>/update/', views.staff_update_complaint_status, name='staff_update_complaint_status'),
    path('staff/complaint/<uuid:reference>/response/', views.staff_add_response, name='staff_add_response'),
    path('staff/profile/', views.staff_profile_view, name='staff_profile_view'),
    path('staff/profile/edit/', views.staff_edit_profile, name='staff_edit_profile'),
    path('staff/feedback/', views.staff_feedback_list, name='staff_feedback_list'),

    # Add more paths for admin/staff/servicom actions as needed
]
