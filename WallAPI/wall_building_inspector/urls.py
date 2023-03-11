from django.urls import path

from wall_building_inspector import views

urlpatterns = [
    path('<int:profile_number>/days/<int:day_number>/', views.ice_data),
    path('<int:profile_number>/overview/<int:day_number>/', views.profile_day_overview),
    path('overview/<int:day_number>/', views.full_day_overview),
    path('overview/', views.full_overview),
]
