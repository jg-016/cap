from apps.calendarios.models import Calendario
from apps.calendarios.models import MembroDeCalendario
from apps.turmas.utils import obter_dados_turma


def _get_dados_calendario(request, calendario: Calendario) -> dict:
    try:
        membro = MembroDeCalendario.objects.get(
            usuario=request.user,
            calendario=calendario
        )
    except MembroDeCalendario.DoesNotExist:
        return {}

    calendarios_ocultos = request.session.get('calendarios_ocultos', [])
    turmas_ocultas = request.session.get('turmas_ocultas', [])

    botao_menu_preenchido = calendario.id not in calendarios_ocultos

    eventos_visiveis = (
        calendario.id not in calendarios_ocultos
        and (
            calendario.turma is None
            or calendario.turma.id not in turmas_ocultas
        )
    )

    dados_calendario = {
        'id': calendario.id,
        'nome': calendario.nome,
        'descricao': calendario.descricao,
        'paleta': membro.numero_paleta,
        'eh_admin': membro.eh_admin,
        'eventos_visiveis': eventos_visiveis,
        'botao_menu_preenchido': botao_menu_preenchido,
    }
    if calendario.turma:
        dados_calendario['turma'] = calendario.turma

    return dados_calendario


def get_dados_calendarios_sem_turma(request):
    if not request.user.is_authenticated:
        return {'calendarios_sem_turma': []}

    dados_calendarios = []

    for calendario in request.user.calendarios.filter(turma=None):
        dados_calendario = _get_dados_calendario(request, calendario)

        if dados_calendario:
            dados_calendarios.append(dados_calendario)

    return {'calendarios_sem_turma': dados_calendarios}

def get_dados_calendarios(request):
    if not request.user.is_authenticated:
        return {'calendarios': []}

    dados_calendarios = []

    for calendario in request.user.calendarios.filter(turma=None):
        dados_calendario = _get_dados_calendario(request, calendario)

        if dados_calendario:
            dados_calendarios.append(dados_calendario)    

    for turma in request.user.turmas.all():
        for calendario in turma.calendarios.all():
            dados_calendario = _get_dados_calendario(request, calendario)

            if dados_calendario:
                dados_calendarios.append(dados_calendario)        

    return {'calendarios': dados_calendarios}


def get_dados_turmas(request):
    if not request.user.is_authenticated:
        return {'turmas': []}

    dados_turmas = []

    for turma in request.user.turmas.all():
        dados_turma = obter_dados_turma(request, turma)

        if dados_turma:
            dados_turmas.append(dados_turma)

    return {'turmas': dados_turmas}