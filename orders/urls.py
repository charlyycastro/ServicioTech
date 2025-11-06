# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"  # requerido para el namespace

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("orden/nueva/", views.order_create, name="create"),
    path("logout/", views.logout_view, name="logout"),  # POST-only
]
