from django.urls import path
from . import views


urlpatterns = [
    path('<int:id>/', views.calendario, name='calendario'),
    path('criar_calendario', views.criar_calendario, name='criar_calendario'),
    path('associar_turma/<int:turma_id>/<int:calendario_id>', views.associar_calendario_turma, name='associar_calendario_turma'),
    path('desassociar_turma/<int:turma_id>/<int:calendario_id>', views.desassociar_calendario_turma, name='desassociar_calendario_turma'),
    path('deletar_calendario/<int:id>', views.deletar_calendario, name='deletar_calendario'),
    path('atualizar_calendario/<int:id>', views.atualizar_calendario, name='atualizar_calendario')
]