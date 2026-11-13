from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from apps.eventos.models import Evento
from apps.calendarios.models import Calendario, MembroDeCalendario


MESES_ptbr = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril',
    'Maio', 'Junho', 'Julho', 'Agosto',
    'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

DIAS_SEMANA_ptbr = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom']


def get_dia_em_foco(request) -> date:
    dia_em_foco_str = request.session.setdefault(
        'dia_em_foco',
        timezone.localdate().isoformat()
    )
    return date.fromisoformat(dia_em_foco_str)


def set_dia_em_foco(request, dia_em_foco: date) -> None:
    request.session['dia_em_foco'] = dia_em_foco.isoformat()


def gerar_context_eventos(
        request, 
        datas: list[date], 
        calendarios: list[Calendario],
        ignorar_ocultos: bool = False
):
    eventos_context = []

    calendarios_visiveis = []

    for calendario in calendarios:
        if ignorar_ocultos:
            calendarios_visiveis.append(calendario)
            continue

        if calendario.id in request.session.get('calendarios_ocultos', []):
            continue

        if calendario.turma != None:
            if calendario.turma.id in request.session.get('turmas_ocultas', []):
                continue

        calendarios_visiveis.append(calendario)

    for calendario in calendarios_visiveis:
        membro_calendario = MembroDeCalendario.objects.filter(
            calendario=calendario,
            usuario=request.user,
        ).first()

        if membro_calendario is None:
            continue

        eventos = Evento.objects.filter(
            calendario=calendario,
            inicio__date__in=[data.isoformat() for data in datas]
        )

        for evento in eventos:
            eventos_context.append({
                'id': evento.id,
                'nome': evento.nome,
                'conteudo': evento.conteudo,
                'inicio': evento.inicio,
                'fim': evento.fim,
                'calendario_id': calendario.id,
                'paleta': membro_calendario.numero_paleta,
            })
        
    return eventos_context


def gerar_context_calendario_geral(request, calendarios: list[Calendario], ignorar_ocultos: bool = False):
    dia_em_foco = get_dia_em_foco(request)
    mes = MESES_ptbr[dia_em_foco.month - 1]
    ano = dia_em_foco.year

    dias_ate_domingo = (dia_em_foco.weekday() + 1) % 7
    ultimo_domingo = dia_em_foco - timedelta(days=dias_ate_domingo)

    datas = []

    for i in range(7):
        data = ultimo_domingo + timedelta(days=i)
        nome = f'{DIAS_SEMANA_ptbr[data.weekday()]} {data.day:02}'

        datas.append( {
            'nome': nome,
            'isoformat': data.isoformat(),
        } )

    horarios = [f'{i:02}:00'for i in range(24)]

    eventos = gerar_context_eventos(
        request=request,
        datas=[ultimo_domingo + timedelta(i) for i in range(7)],
        calendarios=calendarios,
        ignorar_ocultos=ignorar_ocultos
    )

    context = {
        'calendario_geral': {
            'dia_em_foco': dia_em_foco,
            'mes': mes,
            'ano': ano,
            'datas': datas,
            'horarios': horarios,
            'eventos': eventos
        }
    }

    return context


def _voltar_para_pagina_anterior(request):
    # Mantém o usuário na página do calendário geral de onde veio (início, turma ou calendário).
    pagina_anterior = request.META.get('HTTP_REFERER')

    if pagina_anterior and url_has_allowed_host_and_scheme(
        pagina_anterior,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(pagina_anterior)

    return redirect('inicio')


def semana_anterior(request):    
    dia_em_foco = get_dia_em_foco(request)
    set_dia_em_foco(request, dia_em_foco - timedelta(days=7))
    return _voltar_para_pagina_anterior(request)


def proxima_semana(request):
    dia_em_foco = get_dia_em_foco(request)
    set_dia_em_foco(request, dia_em_foco + timedelta(days=7))
    return _voltar_para_pagina_anterior(request)


def voltar_para_hoje(request):
    set_dia_em_foco(request, timezone.localdate())
    return _voltar_para_pagina_anterior(request)