from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("nueva/", views.order_create, name="create"),
    path("<int:pk>/", views.order_detail, name="detail"),
]
