import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from apps.calendarios.models import Calendario
from apps.calendarios.models.membro_de_calendario import MembroDeCalendario
from apps.turmas.models import MembroDeTurma, Turma


@login_required
def calendario(request, id):
    usuario = request.user

    calendario = Calendario.objects.get(id=id)

    membro = MembroDeCalendario.objects.get(
        usuario=usuario,
        calendario=calendario
    )

    membros_calendario = MembroDeCalendario.objects.filter(
        calendario=calendario
    )

    lideres = [
        {
            'nome': membro.usuario.nome_completo,
            'email': membro.usuario.email
        }
        for membro in membros_calendario.filter(eh_admin=True)
    ]

    membros_comuns = [
        {
            'nome': membro.usuario.nome_completo,
            'email': membro.usuario.email
        }
        for membro in membros_calendario.filter(eh_admin=False)
    ]

    eventos = calendario.eventos.all().order_by('inicio')

    eventos_json = json.dumps([
        {
            'id': evento.id,
            'title': evento.nome,
            'description': evento.conteudo,
            'date': evento.inicio.strftime('%Y-%m-%d'),
            'start': evento.inicio.hour + evento.inicio.minute / 60,
            'end': evento.fim.hour + evento.fim.minute / 60,
            'detail_url': reverse(
                'eventos:visualizar_evento', args=[evento.id]
            ),
        }
        for evento in eventos
    ], ensure_ascii=False)

    calendario_context = {
        'id': calendario.id,
        'nome': calendario.nome,
        'descricao': calendario.descricao,
        'turma': calendario.turma,
        'lideres': lideres,
        'membros_comuns': membros_comuns,
        'eventos': eventos,
    }

    usuario_context = {
        'nome': request.user.nome_completo,
        'email': request.user.email,
        'eh_admin': membro.eh_admin,
        'paleta': membro.numero_paleta,
    }

    context = {
        'calendario': calendario_context,
        'usuario': usuario_context,
        'eventos_json': eventos_json,
    }

    return render(
        request,
        'calendarios/calendario.html',
        context
    )


# COLOQUE A FUNÇÃO AQUI
@login_required
def criar_calendario(request):
    usuario = request.user

    numero_calendario = 1

    while True:
        if not usuario.calendarios.filter(
            turma=None,
            nome__icontains=f'Calendário {numero_calendario}'
        ):
            break

        numero_calendario += 1

    nome_calendario = f'Calendário {numero_calendario}'

    calendario = Calendario.objects.create(
        nome=nome_calendario,
        descricao=f'Bem vindo a {nome_calendario}!'
    )

    numero_paleta = usuario.paleta_menos_usada()

    MembroDeCalendario.objects.create(
        usuario=usuario,
        calendario=calendario,
        eh_admin=True,
        numero_paleta=numero_paleta
    )

    return redirect('calendario', calendario.id)


@login_required
def associar_calendario_turma(request, turma_id, calendario_id=None):
    turma = get_object_or_404(Turma, id=turma_id)
    if calendario_id is None:
        calendario_id = request.POST.get('calendario_id') or request.GET.get('calendario_id')
    calendario = get_object_or_404(Calendario, id=calendario_id)

    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para associar calendários a esta turma.')
        return redirect('turma', turma.id)

    calendario.turma = turma
    calendario.save(update_fields=['turma'])
    messages.success(request, 'Calendário associado à turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
def desassociar_calendario_turma(request, turma_id, calendario_id=None):
    turma = get_object_or_404(Turma, id=turma_id)
    if calendario_id is None:
        calendario_id = request.POST.get('calendario_id') or request.GET.get('calendario_id')
    calendario = get_object_or_404(Calendario, id=calendario_id)

    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para remover calendários desta turma.')
        return redirect('turma', turma.id)

    if calendario.turma_id != turma.id:
        messages.error(request, 'Este calendário não está associado a esta turma.')
        return redirect('turma', turma.id)

    calendario.turma = None
    calendario.save(update_fields=['turma'])
    messages.success(request, 'Calendário removido da turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
def atualizar_calendario(request, id):
    usuario = request.user

    calendario = Calendario.objects.get(id=id)

    membro = MembroDeCalendario.objects.get(
        usuario=usuario,
        calendario=calendario
    )

    if membro.eh_admin:
        ...

    return redirect('calendario', id)


@login_required
def deletar_calendario(request, id):
    usuario = request.user

    calendario = Calendario.objects.get(id=id)

    membro = MembroDeCalendario.objects.get(
        usuario=usuario,
        calendario=calendario
    )

    if membro.eh_admin:
        calendario.delete()
    else:
        raise ValueError('O usuário não é admin.')

    return redirect('inicio')