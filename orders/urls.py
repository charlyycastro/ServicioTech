from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("new/", views.order_create, name="create"),
    path("nueva/", views.order_create, name="create_es"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("bulk-delete/", views.bulk_delete, name="bulk_delete"),
    path("logout/", views.logout_view, name="logout"),
]
