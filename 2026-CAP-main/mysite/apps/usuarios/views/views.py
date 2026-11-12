from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect


@login_required
def perfil(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_completo', '').strip()

        if not nome:
            return render(request, 'usuarios/perfil.html', {
                'erro': 'O nome é obrigatório.'
            })
        request.user.nome_completo = nome

        try:
            request.user.full_clean()
            request.user.save(update_fields=['nome_completo'])
        except ValidationError as e:
            return render(request, 'usuarios/perfil.html', {
                'erro': e.messages[0]
            })
        return render(request, 'usuarios/perfil.html', {
            'sucesso': 'Perfil atualizado com sucesso.'
        })
    return render(request, 'usuarios/perfil.html')


@login_required
def alterar_senha(request):
    form = PasswordChangeForm(
        user=request.user,
        data=request.POST or None
    )
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        update_session_auth_hash(request, usuario)

        return render(request, 'usuarios/alterar_senha.html', {
            'form': PasswordChangeForm(user=request.user),
            'sucesso': 'Senha atualizada com sucesso.'})
    return render(request, 'usuarios/alterar_senha.html', {
        'form': form})

@login_required
def excluir_conta(request):
    if request.method == 'POST':
        usuario = request.user
        logout(request)
        usuario.delete()
        return redirect('login')

    return redirect('perfil')