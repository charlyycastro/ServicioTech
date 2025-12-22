from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListView.as_view(), name='user_list'),
    path('crear/', views.UserCreateView.as_view(), name='user_create'),
    path('editar/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    path('eliminar/<int:pk>/', views.UserDeleteView.as_view(), name='user_delete'),
]