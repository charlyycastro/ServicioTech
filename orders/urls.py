from django.urls import path
from .views import OrderListView, order_create, OrderDetailView


app_name = 'orders'
urlpatterns = [
path('', OrderListView.as_view(), name='list'),
path('nuevo/', order_create, name='create'),
path('<slug:folio>/', OrderDetailView.as_view(), name='detail'),
]