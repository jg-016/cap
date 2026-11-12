from django.contrib.auth.decorators import login_required
from .calendario_geral import gerar_context_calendario_geral
from django.shortcuts import render, redirect


@login_required
def inicio(request):
    context = gerar_context_calendario_geral(request, calendarios=request.user.calendarios.all())
    return render(request, 'core/inicio.html', context)