from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('area/<int:area_id>/', views.area_view, name='area_view'),
    path('area/<int:area_id>/<str:view_type>/', views.area_view, name='area_view'),
    path('import/streets/', views.import_streets, name='import_streets'),
    path('import/areas/', views.import_areas, name='import_areas'),
]