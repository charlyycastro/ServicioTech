from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="list"),
    path("orden/nueva/", views.order_create, name="create"),
    path("orden/<int:pk>/", views.ServiceOrderDetailView.as_view(), name="detail"),  # <—
    path("orden/eliminar/", views.order_bulk_delete, name="bulk_delete"),
    path("logout/", views.logout_view, name="logout"),
]