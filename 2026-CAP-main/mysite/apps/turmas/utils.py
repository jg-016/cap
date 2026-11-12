from apps.turmas.models import MembroDeTurma
from apps.turmas.models.turma import Turma


def get_dados_participantes_turmas(request, turma: Turma) -> list:
    dados_membros = []

    try:
        MembroDeTurma.get(usuario=request.user, turma=turma)
    except MembroDeTurma.DoesNotExist:
        return []

    for membro in MembroDeTurma.objects.filter(turma=turma):
        dados = {
            'nome': membro.usuario.nome,
            'email': membro.usuario.email,
            'eh_admin': membro.eh_admin
        }

        dados_membros.append(dados)

    return dados_membros

def obter_dados_turma(request, turma: Turma) -> dict:
    # Importação local para evitar importação circular com apps.core.context_processors.
    from apps.core.context_processors import _get_dados_calendario

    try:
        membro_turma = MembroDeTurma.objects.get(
            usuario=request.user,
            turma=turma
        )
    except MembroDeTurma.DoesNotExist:
        return {}

    calendarios_de_turma = []

    for calendario in turma.calendarios.all():
        dados_calendario = _get_dados_calendario(request, calendario)

        if dados_calendario:
            calendarios_de_turma.append(dados_calendario)

    turmas_ocultas = request.session.get('turmas_ocultas', [])

    botao_menu_preenchido = turma.id not in turmas_ocultas
    eventos_visiveis = turma.id not in turmas_ocultas

    dados_membros = {'lideres': [], 'colegas': []}

    for membro in MembroDeTurma.objects.filter(turma=turma):
        usuario = membro.usuario

        dados_membro = {
            'nome': usuario.nome_completo,
            'email': usuario.email,
        }

        if membro.eh_admin:
            dados_membros['lideres'].append(dados_membro)
        else:
            dados_membros['colegas'].append(dados_membro)

    dados_turma = {
        'id': turma.id,
        'nome': turma.nome,
        'codigo': turma.codigo,
        'descricao': turma.descricao,
        'paleta': membro_turma.numero_paleta,
        'eventos_visiveis': eventos_visiveis,
        'botao_menu_preenchido': botao_menu_preenchido,
        'calendarios': calendarios_de_turma,
        'membros': dados_membros
    }

    return dados_turma
