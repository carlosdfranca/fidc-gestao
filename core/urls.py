from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('limites/', views.limites, name='limites'),
    path('lastro/', views.lastro, name='lastro'),
    path('risco/', views.risco, name='risco'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('conformidade/', views.conformidade, name='conformidade'),
    path('integracoes/', views.integracoes, name='integracoes'),
    path('workflow-cessao/', views.workflow_cessao, name='workflow_cessao'),
]
