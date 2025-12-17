from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # --- NUEVA PORTADA (DASHBOARD) ---
    path("", views.dashboard_view, name="dashboard"), # <--- ESTA ES LA NUEVA PORTADA (/)
    
    # --- LA LISTA VIEJA AHORA ESTÁ EN /orders/list/ ---
    path("list/", views.order_list, name="list"), 
    
    # ... (El resto de tus rutas siguen aquí, revisa que no haya duplicados de la lista) ...
    path("new/", views.order_create, name="create"),
    path("nueva/", views.order_create, name="create_es"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("bulk-delete/", views.bulk_delete, name="bulk_delete"),
    path("logout/", views.logout_view, name="logout"),
    path("<int:pk>/email/", views.email_order, name="email"),
    path('usuarios/', views.user_list_view, name='user_list'),
    path('usuarios/crear/', views.create_user_view, name='create_user'),
    path('usuarios/editar/<int:pk>/', views.edit_user_view, name='edit_user'),
    path('usuarios/eliminar/<int:pk>/', views.delete_user_view, name='delete_user'),
    path('editar/<int:pk>/', views.order_update, name='update'),
    path('<int:pk>/word/', views.download_word, name='download_word'),
]