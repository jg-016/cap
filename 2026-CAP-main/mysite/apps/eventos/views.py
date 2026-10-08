from datetime import datetime

from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.calendarios.models import Calendario
from apps.calendarios.models import MembroDeCalendario
from apps.eventos.models import Evento


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

        if id_calendario is None:
            return redirect('inicio')

        try:
            calendario = Calendario.objects.get(id=int(id_calendario))
        except (TypeError, ValueError, Calendario.DoesNotExist):
            return redirect('inicio')

        if titulo and data and inicio and fim:
            try:
                inicio_dt = datetime.fromisoformat(f'{data}T{inicio}')
                fim_dt = datetime.fromisoformat(f'{data}T{fim}')
                evento = Evento(
                    nome=titulo,
                    conteudo=descricao,
                    inicio=inicio_dt,
                    fim=fim_dt,
                    calendario=calendario,
                )
                evento.full_clean()
                evento.save()
                return redirect('calendario', calendario.id)
            except (ValueError, ValidationError):
                pass
    return redirect('inicio')


@login_required
def visualizar_evento(request, id):
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

    return render(
        request,
        'eventos/visualizar_evento.html',
        {'evento': evento, 'usuario_eh_admin': membro.eh_admin},
    )


@login_required
def deletar_evento(request, id):
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

    if not membro.eh_admin:
        return redirect('eventos:visualizar_evento', id=evento.id)

    if request.method == 'POST':
        evento.delete()
        return redirect('inicio')

    return redirect('eventos:visualizar_evento', id=evento.id)
