from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=CustomAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/owner/', views.OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('dashboard/manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('dashboard/staff/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    # Alias
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('switch-branch/', views.switch_branch, name='switch_branch'),
]
