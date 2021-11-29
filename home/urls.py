from django.urls import path, include
from home import views

app_name = 'home'
urlpatterns = [
    path('',views.MainView.as_view(), name='all'),
    path('main/create/', views.AssetCreate.as_view(), name='asset_create'),
    path('main/<int:pk>/update/', views.AssetUpdate.as_view(), name='asset_update'),
    path('main/<int:pk>/delete/', views.AssetDelete.as_view(), name='asset_delete'),
    path('search/', views.autocomplete)
]