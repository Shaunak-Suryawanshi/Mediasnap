from django.urls import path
from . import views

app_name = 'downloader'

urlpatterns = [
    path('', views.home, name='home'),
    path('fetch-info/', views.fetch_info, name='fetch_info'),
    path('download/', views.start_download, name='download'),
    path('history/', views.history, name='history'),
    path('history/clear/', views.clear_history, name='clear_history'),
    path('history/delete/<int:pk>/', views.delete_history_item, name='delete_history'),
    path('serve/<int:pk>/', views.serve_file, name='serve_file'),
]
