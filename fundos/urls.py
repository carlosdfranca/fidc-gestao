from django.urls import path
from . import views

app_name = 'fundos'

urlpatterns = [
    path('cota/<uuid:fundo_id>/', views.calcular_cota_manual, name='calcular_cota_manual'),
    path('aplicacao/nova/', views.nova_aplicacao, name='nova_aplicacao'),
    path('resgate/novo/', views.novo_resgate, name='novo_resgate'),
]