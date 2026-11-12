from datetime import datetime

from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.http import require_GET, require_POST

from apps.calendarios.models import Calendario
from apps.calendarios.models import MembroDeCalendario
from apps.eventos.models import Evento


def _buscar_evento_e_membro(request, id):
    """Retorna (evento, membro) ou 404 se o usuário não participa do calendário."""
    evento = get_object_or_404(
        Evento.objects.select_related('calendario'),
        id=id,
        calendario__usuarios=request.user,
    )
    membro = get_object_or_404(
        MembroDeCalendario,
        calendario=evento.calendario,
        usuario=request.user,
    )
    return evento, membro


@login_required
def criar_evento(request):
    if request.method == 'POST':

        titulo = request.POST.get('titulo', '').strip()
        data = request.POST.get('data')
        inicio = request.POST.get('inicio')
        fim = request.POST.get('fim')
        descricao = request.POST.get('descricao', '').strip()
        id_calendario = (
            request.POST.get('id-calendario')
            or request.POST.get('id_calendario')
            or request.POST.get('calendario')
        )

        try:
            calendario_id = int(id_calendario)
        except (TypeError, ValueError):
            return redirect('inicio')

        calendario = get_object_or_404(
            Calendario.objects.filter(usuarios=request.user),
            id=calendario_id,
        )

        if titulo and data and inicio and fim:

            try:
                inicio_dt = datetime.fromisoformat(
                    f'{data}T{inicio}'
                )
                fim_dt = datetime.fromisoformat(
                    f'{data}T{fim}'
                )
                evento = Evento(
                    nome=titulo,
                    conteudo=descricao,
                    inicio=inicio_dt,
                    fim=fim_dt,
                    calendario=calendario,
                )
                evento.full_clean()
                evento.save()
            except (ValueError, ValidationError):
                pass
        return redirect('calendario', calendario.id)
    return redirect('inicio')


@login_required
@require_GET
def detalhes_evento(request, id):
    """Dados do evento em JSON, usados pelo modal de detalhes."""
    evento, membro = _buscar_evento_e_membro(request, id)

    inicio = timezone.localtime(evento.inicio)
    fim = timezone.localtime(evento.fim)

    return JsonResponse({
        'id': evento.id,
        'titulo': evento.nome,
        'descricao': evento.conteudo,
        'data': inicio.strftime('%Y-%m-%d'),
        'inicio': inicio.strftime('%H:%M'),
        'fim': fim.strftime('%H:%M'),
        'calendario': evento.calendario.nome,
        'pode_editar': membro.eh_admin,
        'url_atualizar': reverse('eventos:atualizar_evento', args=[evento.id]),
    })


@login_required
@require_POST
def atualizar_evento(request, id):
    evento, membro = _buscar_evento_e_membro(request, id)

    # A permissão é checada aqui no servidor; esconder o botão não basta.
    if not membro.eh_admin:
        return JsonResponse(
            {'erros': {'__all__': ['Você não tem permissão para editar este evento.']}},
            status=403,
        )

    titulo = request.POST.get('titulo', '').strip()
    descricao = request.POST.get('descricao', '').strip()
    data = parse_date(request.POST.get('data', ''))
    inicio = parse_time(request.POST.get('inicio', ''))
    fim = parse_time(request.POST.get('fim', ''))

    erros = {}
    if not titulo:
        erros['titulo'] = ['Informe o título do evento.']
    elif len(titulo) > 100:
        erros['titulo'] = ['O título pode ter no máximo 100 caracteres.']
    if len(descricao) > 500:
        erros['descricao'] = ['A descrição pode ter no máximo 500 caracteres.']
    if data is None:
        erros['data'] = ['Informe uma data válida.']
    if inicio is None:
        erros['inicio'] = ['Informe o horário de início.']
    if fim is None:
        erros['fim'] = ['Informe o horário de término.']

    if erros:
        return JsonResponse({'erros': erros}, status=400)

    evento.nome = titulo
    evento.conteudo = descricao
    # Datetimes "naive", igual ao criar_evento: o Django interpreta no
    # TIME_ZONE do settings ao salvar.
    evento.inicio = datetime.combine(data, inicio)
    evento.fim = datetime.combine(data, fim)

    try:
        evento.full_clean()
    except ValidationError as erro:
        return JsonResponse({'erros': {'__all__': erro.messages}}, status=400)

    evento.save()
    return JsonResponse({'ok': True})


@login_required
def deletar_evento(request, id):
    evento, membro = _buscar_evento_e_membro(request, id)

    if not membro.eh_admin:
        return redirect('calendario', evento.calendario.id)

    if request.method == 'POST':
        evento.delete()
        return redirect('inicio')

    return redirect('calendario', evento.calendario.id)