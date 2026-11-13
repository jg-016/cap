from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST

from apps.turmas.models import Turma, MembroDeTurma
from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.turmas.utils import obter_dados_turma
from apps.core.views import gerar_context_calendario_geral


PALETAS_TURMA = [
    (1, 'Vermelho'),
    (2, 'Laranja'),
    (3, 'Verde'),
    (4, 'Azul'),
    (5, 'Ciano'),
    (6, 'Violeta'),
    (7, 'Rosa'),
]


def _sincronizar_membros_calendario_turma(turma, calendario):
    for membro_turma in MembroDeTurma.objects.filter(turma=turma):
        membro_calendario, criado = MembroDeCalendario.objects.get_or_create(
            usuario=membro_turma.usuario,
            calendario=calendario,
            defaults={
                'eh_admin': membro_turma.eh_admin,
                'numero_paleta': membro_turma.numero_paleta,
            },
        )

        if not criado and membro_calendario.numero_paleta != membro_turma.numero_paleta:
            membro_calendario.numero_paleta = membro_turma.numero_paleta
            membro_calendario.save(update_fields=['numero_paleta'])


@login_required
def turma(request, id):
    turma = get_object_or_404(Turma, id=id)
    membro_turma = get_object_or_404(
        MembroDeTurma,
        usuario=request.user,
        turma=turma,
    )
    membro = membro_turma.eh_admin

    dados_turma = obter_dados_turma(request, turma)
    dados_membros = dados_turma.pop('membros')
    
    context = {
        'turma': dados_turma,
        'painel_membros': dados_membros,
        'usuario_eh_admin': membro,
        'pode_remover_participantes': membro,
        'calendarios_disponiveis': request.user.calendarios.filter(turma__isnull=True),
        'paletas_disponiveis': PALETAS_TURMA,
    }
    
    context_calendario_geral = gerar_context_calendario_geral(
        request, calendarios=turma.calendarios.all()
    )
    context.update(context_calendario_geral)

    return render(request, 'turmas/turma.html', context)


@login_required
def criar_turma(request):
    usuario = request.user

    numero_turma = 1
    while True:
        if not usuario.turmas.filter(nome__icontains=f'Turma {numero_turma}'):
            break
        numero_turma += 1
    nome_turma = f'Turma {numero_turma}'

    turma = Turma.objects.create(
        nome=nome_turma,
        descricao=f'Bem vindo a {nome_turma}!'
    )

    numero_paleta = usuario.paleta_menos_usada()

    MembroDeTurma.objects.create(
        usuario=usuario,
        turma=turma,
        eh_admin=True,
        numero_paleta=numero_paleta
    )

    return redirect('turma', turma.id)


@login_required
def atualizar_turma(request, id):
    usuario = request.user
    turma = get_object_or_404(Turma, id=id)
    membro = get_object_or_404(MembroDeTurma, usuario=usuario, turma=turma)

    if membro.eh_admin:
        if request.method == 'POST':
            try:
                numero_paleta = int(request.POST.get('numero_paleta', membro.numero_paleta))
            except (TypeError, ValueError):
                numero_paleta = None

            if numero_paleta not in range(1, 8):
                messages.error(request, 'Selecione uma cor válida para a turma.')
                return redirect('turma', id)

            turma.nome = request.POST.get('nome', '').strip()
            turma.descricao = request.POST.get('descricao', '').strip()

            try:
                turma.full_clean()
            except ValidationError as erro:
                messages.error(request, erro)
            else:
                turma.save(update_fields=['nome', 'descricao'])
                membro.numero_paleta = numero_paleta
                membro.save(update_fields=['numero_paleta'])
                MembroDeCalendario.objects.filter(
                    usuario=usuario,
                    calendario__turma=turma,
                ).update(numero_paleta=numero_paleta)
                messages.success(request, 'Turma atualizada com sucesso.')
    else:
        messages.error(request, 'Somente administradores podem atualizar a turma.')

    return redirect('turma', id)


@login_required

@login_required
@require_POST
def deletar_turma(request, id):
    turma = get_object_or_404(Turma, id=id)

    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,).first()

    if not membro:
        messages.error(request, 'Somente administradores podem excluir a turma.')
        return redirect('turma', id)
    turma.delete()
    return redirect('inicio')


@login_required
@require_POST
def adicionar_calendario_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para adicionar calendários a esta turma.')
        return redirect('turma', turma.id)

    try:
        calendario_id = int(request.POST.get('calendario_id'))
    except (TypeError, ValueError):
        messages.error(request, 'Selecione um calendário válido.')
        return redirect('turma', turma.id)

    calendario = get_object_or_404(Calendario, id=calendario_id)
    if calendario.turma_id == turma.id:
        messages.info(request, 'Este calendário já está associado a esta turma.')
        return redirect('turma', turma.id)
    if calendario.turma_id is not None:
        messages.error(request, 'Este calendário já pertence a outra turma e não pode ser associado a esta.')
        return redirect('turma', turma.id)
    if not MembroDeCalendario.objects.filter(
        usuario=request.user,
        calendario=calendario,
    ).exists():
        messages.error(request, 'Você não tem acesso a este calendário.')
        return redirect('turma', turma.id)

    calendario.turma = turma
    calendario.save(update_fields=['turma'])
    _sincronizar_membros_calendario_turma(turma, calendario)

    messages.success(request, 'Calendário associado à turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
@require_POST
def criar_calendario_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para criar calendários para esta turma.')
        return redirect('turma', turma.id)

    nome = (request.POST.get('nome') or '').strip()
    descricao = (request.POST.get('descricao') or '').strip()

    if not nome:
        messages.error(request, 'Informe o nome do calendário para criar para a turma.')
        return redirect('turma', turma.id)

    calendario = Calendario.objects.create(
        nome=nome,
        descricao=descricao or 'Calendário criado para a turma.',
        turma=turma,
    )

    _sincronizar_membros_calendario_turma(turma, calendario)

    messages.success(request, 'Calendário criado e associado à turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
@require_POST
def remover_calendario_turma(request, turma_id=None, calendario_id=None):
    turma = get_object_or_404(Turma, id=turma_id)
    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para remover calendários desta turma.')
        return redirect('turma', turma.id)

    calendario_id = calendario_id or request.POST.get('calendario_id')
    if not calendario_id:
        messages.error(request, 'Selecione um calendário para remover da turma.')
        return redirect('turma', turma.id)

    try:
        calendario_id = int(calendario_id)
    except (TypeError, ValueError):
        messages.error(request, 'Selecione um calendário válido.')
        return redirect('turma', turma.id)

    calendario = get_object_or_404(Calendario, id=calendario_id)
    if calendario.turma_id != turma.id:
        messages.error(request, 'Este calendário não está associado a esta turma.')
        return redirect('turma', turma.id)

    calendario.delete()
    messages.success(request, 'Calendário removido da turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
@require_POST
def remover_participante_turma(request, turma_id, usuario_id):
    turma = get_object_or_404(Turma, id=turma_id)
    admin = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not admin:
        messages.error(request, 'Você não tem permissão para remover participantes desta turma.')
        return redirect('turma', turma.id)

    if request.user.id == usuario_id:
        messages.error(request, 'Você não pode remover a si mesmo da turma. Use a opção de sair da turma.')
        return redirect('turma', turma.id)

    membro = get_object_or_404(MembroDeTurma, turma=turma, usuario_id=usuario_id)

    if membro.eh_admin:
        messages.error(request, 'Administradores não podem remover outros administradores da turma.')
        return redirect('turma', turma.id)

    with transaction.atomic():
        membro.delete()
        MembroDeCalendario.objects.filter(
            usuario_id=usuario_id,
            calendario__turma=turma,
        ).delete()

    messages.success(request, f'{membro.usuario.nome_completo} foi removido da turma.')
    return redirect('turma', turma.id)