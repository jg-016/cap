from django.urls import path
from .views import (
    atualizar_evento,
    criar_evento,
    deletar_evento,
    detalhes_evento,
)

app_name = 'eventos'

urlpatterns = [
    path('criar/', criar_evento, name='criar_evento'),
    path('<int:id>/detalhes/', detalhes_evento, name='detalhes_evento'),
    path('<int:id>/atualizar/', atualizar_evento, name='atualizar_evento'),
    path('<int:id>/deletar/', deletar_evento, name='deletar_evento'),
]