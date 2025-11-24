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
    path("<int:pk>/email/", views.email_order, name="email"),
    path('usuarios/', views.user_list_view, name='user_list'),          # Lista
    path('usuarios/crear/', views.create_user_view, name='create_user'),# Crear
    path('usuarios/editar/<int:pk>/', views.edit_user_view, name='edit_user'), # Editar
    path('usuarios/eliminar/<int:pk>/', views.delete_user_view, name='delete_user'), # Eliminar
]
