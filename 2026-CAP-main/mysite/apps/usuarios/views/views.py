from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from apps.usuarios.models.usuario import Usuario


@login_required
def perfil(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip()
        if not nome or not email:
            return render(request, 'usuarios/perfil.html', {
                'erro': 'Nome e e-mail são obrigatórios.'
            })

        if Usuario.objects.filter(email=email).exclude(id=request.user.id).exists():
            return render(request, 'usuarios/perfil.html', {
                'erro': 'Este e-mail já está sendo usado.'})
        request.user.nome_completo = nome
        request.user.email = email
        try:
            request.user.full_clean()
            request.user.save(update_fields=['nome_completo', 'email'])
        except ValidationError as e:
            return render(request, 'usuarios/perfil.html', {
                'erro': e.messages[0]})
        return render(request, 'usuarios/perfil.html', {
            'sucesso': 'Perfil atualizado com sucesso.'})
    return render(request, 'usuarios/perfil.html')

@login_required
def excluir_conta(request):
    if request.method == 'POST':
        usuario = request.user
        logout(request)
        usuario.delete()
        return redirect('login')
    return redirect('perfil')