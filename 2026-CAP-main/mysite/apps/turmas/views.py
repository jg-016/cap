from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render, redirect

from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.turmas.models import Turma, MembroDeTurma
from apps.core.context_processors import _get_dados_turma
from apps.core.views import gerar_context_calendario_geral


@login_required
def turma(request, id):
    turma = get_object_or_404(Turma, id=id)
    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).exists()
    
    context = {
        'turma': _get_dados_turma(request, turma, incluir_membros=True),
        'usuario_eh_admin': membro,
        'calendarios_disponiveis': request.user.calendarios.filter(turma__isnull=True),
    }
    
    context_calendario_geral = gerar_context_calendario_geral(
        request, calendarios=turma.calendarios.all()
    )
    context.update(context_calendario_geral)

    return render(request, 'turmas/turma.html', context)


@login_required
def adicionar_calendario_turma(request, turma_id=None, calendario_id=None):
    turma = get_object_or_404(Turma, id=turma_id)
    membro = MembroDeTurma.objects.filter(
        usuario=request.user,
        turma=turma,
        eh_admin=True,
    ).first()

    if not membro:
        messages.error(request, 'Você não tem permissão para adicionar calendários a esta turma.')
        return redirect('turma', turma.id)

    if calendario_id is None:
        calendario_id = request.POST.get('calendario_id') or request.GET.get('calendario_id')

    nome = (request.POST.get('nome') or '').strip()
    descricao = (request.POST.get('descricao') or '').strip()

    if calendario_id:
        calendario = get_object_or_404(Calendario, id=calendario_id)
        if calendario.turma_id == turma.id:
            messages.info(request, 'Este calendário já está associado a esta turma.')
            return redirect('turma', turma.id)
        if calendario.turma_id is not None and calendario.turma_id != turma.id:
            messages.error(request, 'Este calendário já pertence a outra turma e não pode ser associado a esta.')
            return redirect('turma', turma.id)

        calendario.turma = turma
        calendario.save(update_fields=['turma'])

        for membro_turma in MembroDeTurma.objects.filter(turma=turma):
            MembroDeCalendario.objects.get_or_create(
                usuario=membro_turma.usuario,
                calendario=calendario,
                defaults={
                    'eh_admin': membro_turma.eh_admin,
                    'numero_paleta': membro_turma.usuario.paleta_menos_usada(),
                },
            )

        messages.success(request, 'Calendário associado à turma com sucesso.')
        return redirect('turma', turma.id)

    if not nome:
        messages.error(request, 'Informe o nome do calendário para criar e associar a turma.')
        return redirect('turma', turma.id)

    calendario = Calendario.objects.create(
        nome=nome,
        descricao=descricao or 'Calendário criado para a turma.',
        turma=turma,
    )

    MembroDeCalendario.objects.get_or_create(
        usuario=request.user,
        calendario=calendario,
        defaults={
            'eh_admin': True,
            'numero_paleta': request.user.paleta_menos_usada(),
        },
    )

    for membro_turma in MembroDeTurma.objects.filter(turma=turma):
        MembroDeCalendario.objects.get_or_create(
            usuario=membro_turma.usuario,
            calendario=calendario,
            defaults={
                'eh_admin': membro_turma.eh_admin,
                'numero_paleta': membro_turma.usuario.paleta_menos_usada(),
            },
        )

    messages.success(request, 'Calendário criado e associado à turma com sucesso.')
    return redirect('turma', turma.id)


@login_required
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

    if calendario_id is None:
        calendario_id = request.POST.get('calendario_id') or request.GET.get('calendario_id')

    calendario = get_object_or_404(Calendario, id=calendario_id)

    if calendario.turma_id != turma.id:
        messages.error(request, 'Este calendário não está associado a esta turma.')
        return redirect('turma', turma.id)

    calendario.turma = None
    calendario.save(update_fields=['turma'])
    messages.success(request, 'Calendário removido da turma com sucesso.')
    return redirect('turma', turma.id)


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
            turma.nome = request.POST.get('nome', '').strip()
            turma.descricao = request.POST.get('descricao', '').strip()

            try:
                turma.full_clean()
            except ValidationError as erro:
                messages.error(request, erro)
            else:
                turma.save(update_fields=['nome', 'descricao'])
                messages.success(request, 'Turma atualizada com sucesso.')
    else:
        messages.error(request, 'Somente administradores podem atualizar a turma.')

    return redirect('turma', id)


@login_required
def deletar_turma(request, id):
    usuario = request.user
    turma = Turma.objects.get(id=id)
    membro = MembroDeTurma.objects.get(usuario=usuario, turma=turma)

    if membro.eh_admin:
        turma.delete()
    else:
        raise ValueError('O usuário não é admin.')

    return redirect('inicio')