from django.urls import path

from accounts import views

urlpatterns = [
    path("auth/google/", views.GoogleLoginView.as_view(), name="auth-google"),
    path("auth/refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("departments/", views.DepartmentListView.as_view(), name="departments"),
]
