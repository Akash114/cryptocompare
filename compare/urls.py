from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [

    path('',views.home,name='index'),
    path('data_table',views.data_table,name='dataTable'),
    path('api/get_all',views.get_all,name="getAll"),
    path('api/get_data',views.get_data,name="getData")
]