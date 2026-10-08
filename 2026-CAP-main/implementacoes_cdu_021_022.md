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

## 8) Organização do botão "Criar evento"

O botão foi movido para a barra de navegação do calendário, ao lado dos controles de semana, e recebeu dimensões compactas, estilo consistente, estado de foco visível e ajuste responsivo para telas estreitas.

Arquivos:
- `mysite/apps/core/templates/core/calendario_geral.html`
- `mysite/apps/core/static/core/css/calendario_geral.css`

Trecho do template:

```django
<div class="ferramentas-navegacao">
    <h2 class="mes-em-foco">{{ calendario_geral.mes }} {{ calendario_geral.ano }}</h2>
    <a href="{% url 'voltar_para_hoje' %}" class="voltar-para-hoje">Hoje</a>
    <a href="{% url 'semana_anterior' %}" class="icone-semana-anterior material-symbols-outlined">arrow_back_ios_new</a>
    <a href="{% url 'proxima_semana' %}" class="icone-proxima-semana material-symbols-outlined">arrow_forward_ios</a>
    <button type="button" class="botao-criar-evento">+ Criar evento</button>
</div>
```

Estilos do botão:

```css
.ferramentas-navegacao .botao-criar-evento {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    width: auto;
    min-height: 36px;
    margin-left: 12px;
    padding: 7px 14px;
    border: 0;
    border-radius: 10px;
    background-color: #288012;
    color: #fff;
    font: inherit;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
    cursor: pointer;
}

.ferramentas-navegacao .botao-criar-evento:hover {
    background-color: #20660e;
}
```

## 9) Correção de eventos sobrepostos à lista de membros

Ao abrir um calendário existente associado a uma turma, eventos apareciam visualmente sobre as listas de líderes e membros. A grade tinha linhas de 30 px por hora, mas o posicionamento e a altura dos eventos usavam 60 px por hora. Agora os eventos usam a mesma escala vertical da grade.

Arquivo: `mysite/apps/calendarios/templates/calendarios/calendario.html`

```javascript
const PIXELS_PER_HOUR = 30;

block.style.top = `${event.start * PIXELS_PER_HOUR}px`;
block.style.height = `${(event.end - event.start) * PIXELS_PER_HOUR}px`;
```

## 10) Organização dos calendários e ações na página da turma

A seção “Calendários da turma” passou a ser um painel organizado com botões para associar calendário existente e criar calendário. Os calendários vinculados são exibidos em cartões com indicador de cor e ação de remoção. Em telas estreitas, o painel reorganiza os botões e cartões em uma coluna.

As ações administrativas agora abrem diálogos popup no padrão nativo `<dialog>` do projeto:
- **Associar calendário** abre um formulário de seleção.
- **Criar calendário** abre um formulário de nome e descrição.
- **Remover** abre confirmação por calendário; a confirmação esclarece que o calendário e os eventos não serão excluídos.

Arquivos:
- Template e diálogos: `mysite/apps/turmas/templates/turmas/turma.html`
- Estilos: `mysite/apps/turmas/static/turmas/css/calendarios_turma.css`
- Abertura e fechamento dos diálogos: `mysite/apps/turmas/static/turmas/js/modal_calendarios_turma.js`

Botões que abrem os popups:

```django
<button type="button" data-abrir-modal="modal-associar-calendario-turma">
    Associar calendário
</button>
<button type="button" data-abrir-modal="modal-criar-calendario-turma">
    Criar calendário
</button>
```

Cada cartão abre uma confirmação associada ao calendário correspondente:

```django
<button
    type="button"
    data-abrir-modal="modal-remover-calendario-{{ calendario.id }}"
>
    Remover
</button>
```

O JavaScript usa o identificador dos botões dentro do painel para abrir o `<dialog>` correspondente e fecha o popup pelos botões de cancelar/fechar ou pelo clique no backdrop. Esse escopo mantém separado o modal de edição da turma. Os formulários mantêm os endpoints POST existentes e incluem proteção CSRF.

### Compactação visual do painel

O painel foi compactado reduzindo margens, espaçamento, tamanho do título, botões e cartões. Foram removidas as frases auxiliares em cinza do cabeçalho e os avisos cinza para lista vazia ou ausência de calendários pessoais disponíveis.

### Ajustes no popup e destaque do calendário

O popup de associação ficou um pouco mais largo, com `box-sizing: border-box` e o `select` limitado à largura interna disponível para evitar que o controle ultrapasse o popup. Na página da turma, o calendário agora fica dentro de um painel com borda, fundo e toolbar destacados, dando maior hierarquia visual à agenda.

Arquivo de estilos: `mysite/apps/turmas/static/turmas/css/calendarios_turma.css`.

O formulário de associação também usa uma coluna CSS `minmax(0, 1fr)`, e o campo do select tem `min-width: 0`, `max-width: 100%` e `width: 100%` para conter a largura intrínseca do controle dentro do popup.

## 11) Rolagem e hierarquia visual dos calendários

O layout global agora mantém a rolagem do menu lateral independente da área principal; a área principal rola verticalmente e evita overflow horizontal. A grade semanal tem uma área rolável delimitada, e o calendário compartilhado pelas páginas de turma tem altura máxima relativa à janela, permitindo rolar a grade sem deslocar o menu lateral.

Nas páginas de calendário, o título, a turma associada e a descrição foram movidos para antes da grade semanal para ficarem visíveis no topo, em vez de aparecerem depois de toda a grade. Como o calendário geral é incluído pelo mesmo template em todas as turmas, o ajuste do calendário de turma aplica-se a todas elas.

Arquivos principais:
- `mysite/apps/core/static/core/css/base.css`
- `mysite/apps/core/static/core/css/menu_lateral.css`
- `mysite/apps/core/static/core/css/calendario_geral.css`
- `mysite/apps/turmas/static/turmas/css/calendarios_turma.css`
- `mysite/apps/calendarios/static/calendarios/css/calendario.css`
- `mysite/apps/calendarios/templates/calendarios/calendario.html`
