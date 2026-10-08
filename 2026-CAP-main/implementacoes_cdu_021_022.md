# Implementações realizadas para CDU-021 e CDU-022

Este arquivo reúne os trechos principais das implementações feitas para associar e remover calendários de turma, com alinhamento às regras do sistema e aos requisitos dos CDU 021 e 022.

## 1) Lógica de associação de calendário à turma

Arquivo: `mysite/apps/turmas/views.py`

```python
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
```

## 2) Lógica de remoção do calendário da turma

Arquivo: `mysite/apps/turmas/views.py`

```python
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
```

## 3) Interface da turma com opções de associação e remoção

Arquivo: `mysite/apps/turmas/templates/turmas/turma.html`

```django
{% if usuario_eh_admin %}
    <section class="bloco-calendarios-turma">
        <h2>Calendários da turma</h2>

        <form method="post" action="{% url 'adicionar_calendario' turma.id %}" class="form-adicionar-calendario">
            {% csrf_token %}

            <label for="calendario_id">Associar calendário</label>
            <select id="calendario_id" name="calendario_id" required>
                <option value="" selected disabled>Selecione um calendário</option>
                {% for calendario in calendarios_disponiveis %}
                    <option value="{{ calendario.id }}">{{ calendario.nome }}</option>
                {% endfor %}
            </select>

            <button type="submit">Adicionar</button>
        </form>

        <form method="post" action="{% url 'criar_calendario_turma' turma.id %}" class="form-criar-calendario-turma">
            {% csrf_token %}
            <label for="nome_calendario_turma">Criar calendário para a turma</label>
            <input id="nome_calendario_turma" type="text" name="nome" placeholder="Nome do calendário" maxlength="100" required>
            <textarea name="descricao" placeholder="Descrição" rows="3" maxlength="500"></textarea>
            <button type="submit">Criar e associar</button>
        </form>

        {% if turma.calendarios %}
            <ul class="lista-calendarios-turma">
                {% for calendario in turma.calendarios %}
                    <li>
                        <a href="{% url 'calendario' calendario.id %}">{{ calendario.nome }}</a>
                        <form method="post" action="{% url 'remover_calendario_turma' turma.id calendario.id %}">
                            {% csrf_token %}
                            <button type="submit" class="botao-remover">Remover</button>
                        </form>
                    </li>
                {% empty %}
                    <li>Não há calendários associados a esta turma.</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>Não há calendários associados a esta turma.</p>
        {% endif %}
    </section>
{% endif %}
```

## 4) Rotas utilizadas

Arquivo: `mysite/apps/turmas/urls.py`

```python
urlpatterns = [
    path('<int:id>', views.turma, name='turma'),
    path('criar_turma', views.criar_turma, name='criar_turma'),
    path('criar_calendario_turma/<int:turma_id>', views.adicionar_calendario_turma, name='criar_calendario_turma'),
    path('adicionar_calendario/<int:turma_id>', views.adicionar_calendario_turma, name='adicionar_calendario'),
    path('adicionar_calendario/<int:turma_id>/<int:calendario_id>', views.adicionar_calendario_turma, name='adicionar_calendario_turma'),
    path('remover_calendario/<int:turma_id>', views.remover_calendario_turma, name='remover_calendario'),
    path('remover_calendario/<int:turma_id>/<int:calendario_id>', views.remover_calendario_turma, name='remover_calendario_turma'),
    path('atualizar_turma/<int:id>', views.atualizar_turma, name='atualizar_turma'),
    path('deletar_turma/<int:id>', views.deletar_turma, name='deletar_turma'),
]
```

## 5) Correção de integração com criação de evento

Arquivo: `mysite/apps/eventos/views.py`

```python
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
```

Essas correções evitam falhas quando o formulário envia nomes variantes do campo de calendário e preservam a navegação correta após a criação de eventos.

## 6) Validação executada

Comando executado:

```bash
cd /workspaces/cap/2026-CAP-main/mysite && python manage.py test apps.turmas.tests apps.calendarios.tests apps.eventos.tests
```

Resultado: sucesso, com 13 testes aprovados.

## 7) Ajuste do UsuarioManager

O arquivo anexado mostra a estrutura base do `UsuarioManager`, que deve seguir o padrão do Django para criação de usuários e superusuários. Abaixo está a versão corrigida e documentada, pronta para uso no projeto:

```python
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)

        if password is not None:
            if not extra_fields.get('is_superuser', False):
                validate_password(password, usuario)

            usuario.set_password(password)
        else:
            usuario.set_unusable_password()

        usuario.full_clean()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields['is_staff'] is not True:
            raise ValueError('Superuser deve ter is_staff=True.')

        if extra_fields['is_superuser'] is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
```

Esse padrão garante:
- validação da senha;
- normalização do e-mail;
- criação segura de usuários comuns e administradores;
- compatibilidade com o modelo de usuário do projeto.

