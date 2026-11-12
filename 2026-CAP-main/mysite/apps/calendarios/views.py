import json

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods

from apps.calendarios.forms import CalendarioForm
from apps.calendarios.models import Calendario
from apps.calendarios.models.membro_de_calendario import MembroDeCalendario
from apps.core.views import gerar_context_calendario_geral


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
        }
        for evento in eventos
    ], ensure_ascii=False)
    # Mesmo formato usado pelo painel de membros da turma (core/painel_membros.html).
    painel_membros = {
        'lideres': [
            {
                'nome': membro_calendario.usuario.nome_completo,
                'email': membro_calendario.usuario.email
            }
            for membro_calendario in membros_calendario.filter(eh_admin=True)
        ],
        'colegas': [
            {
                'nome': membro_calendario.usuario.nome_completo,
                'email': membro_calendario.usuario.email
            }
            for membro_calendario in membros_calendario.filter(eh_admin=False)
        ],
    }

    calendario_context = {
        'id': calendario.id,
        'nome': calendario.nome,
        'descricao': calendario.descricao,
        'turma': calendario.turma,
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
        'painel_membros': painel_membros,
    }

    # Na página do próprio calendário, os eventos aparecem mesmo se ele estiver oculto no menu lateral.
    context.update(gerar_context_calendario_geral(
        request, calendarios=[calendario], ignorar_ocultos=True
    ))

    return render(
        request,
        'calendarios/calendario.html',
        context
    )


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
@require_http_methods(['GET', 'POST'])
def atualizar_calendario(request, id):
    calendario = get_object_or_404(Calendario, id=id)
    membro = MembroDeCalendario.objects.filter(
        usuario=request.user,
        calendario=calendario,
    ).first()

    if not membro or not membro.eh_admin:
        return HttpResponseForbidden(
            'Somente administradores podem atualizar este calendário.'
        )

    dados = request.POST if request.method == 'POST' else None
    form = CalendarioForm(dados, instance=calendario)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Calendário atualizado com sucesso.')
        return redirect('calendario', id=id)

    return render(
        request,
        'calendarios/atualizar_calendario.html',
        {
            'calendario': calendario,
            'form': form,
            'paleta': membro.numero_paleta,
        },
    )


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