from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ================================================================
    # VISTAS PRINCIPALES Y AUTENTICACIÓN
    # ================================================================
    path("", views.dashboard_view, name="dashboard"),  # Portada (/)
    path("list/", views.order_list, name="list"),      # Lista de Órdenes
    path("logout/", views.logout_view, name="logout"), # Cierre de Sesión

    # ================================================================
    # GESTIÓN DE ÓRDENES (CRUD)
    # ================================================================
    # CREATE
    path("new/", views.order_create, name="create"),
    path("nueva/", views.order_create, name="create_es"), 
    
    # UPDATE
    path("editar/<int:pk>/", views.order_update, name="update"),
    
    # READ (Detail)
    path("<int:pk>/", views.order_detail, name="detail"),       

    # ================================================================
    # UTILIDADES Y ACCIONES DE ORDEN
    # ================================================================
    path("bulk-delete/", views.bulk_delete, name="bulk_delete"),
    path("<int:pk>/email/", views.email_order, name="email"),

    # ================================================================
    # GESTIÓN DE USUARIOS
    # ================================================================
    path('usuarios/', views.user_list_view, name='user_list'),
    path('usuarios/crear/', views.create_user_view, name='create_user'),
    path('usuarios/editar/<int:pk>/', views.edit_user_view, name='edit_user'),
    path('usuarios/eliminar/<int:pk>/', views.delete_user_view, name='delete_user'),
]