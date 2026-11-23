from django.urls import path

from catalog import views

urlpatterns = [
    path("me/access/", views.MyAccessView.as_view(), name="my-access"),
]
