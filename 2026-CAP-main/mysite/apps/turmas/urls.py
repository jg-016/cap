from django.urls import path
from . import views

urlpatterns = [
    path('<int:id>', views.turma, name='turma'),
    path('criar_turma', views.criar_turma, name='criar_turma'),
    path('criar_calendario_turma/<int:turma_id>', views.adicionar_calendario_turma, name='criar_calendario_turma'),
    path('adicionar_calendario/<int:turma_id>', views.adicionar_calendario_turma, name='adicionar_calendario'),
    path('adicionar_calendario/<int:turma_id>/<int:calendario_id>', views.adicionar_calendario_turma, name='adicionar_calendario_turma'),
    path('remover_calendario/<int:turma_id>', views.remover_calendario_turma, name='remover_calendario'),
    path('remover_calendario/<int:turma_id>/<int:calendario_id>', views.remover_calendario_turma, name='remover_calendario_turma'),
    path('atualizar_turma/<int:id>', views.atualizar_turma, name='atualizar_turma'),
    path('deletar_turma/<int:id>', views.deletar_turma, name='deletar_turma'),
]