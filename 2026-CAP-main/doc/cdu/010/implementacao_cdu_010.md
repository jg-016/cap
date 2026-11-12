# Implementação do CDU-010 — Atualizar calendário

Este guia registra a implementação do fluxo de edição descrito em
[cdu_010.md](cdu_010.md) e nos [diagramas](diagramas_cdu_010.md). A funcionalidade
permite que um administrador atualize o nome e a descrição de um calendário,
preserva o formulário quando há erros e impede alterações por outros usuários.

## Arquivos alterados e criados

| Arquivo | Responsabilidade |
| --- | --- |
| `mysite/apps/calendarios/forms.py` | Formulário de modelo com os campos nome e descrição. |
| `mysite/apps/calendarios/views.py` | Busca o calendário, autoriza, valida, salva e redireciona. |
| `mysite/apps/calendarios/templates/calendarios/atualizar_calendario.html` | Formulário HTML, exibição de erros e ação de cancelamento. |
| `mysite/apps/calendarios/static/calendarios/css/atualizar_calendario.css` | Estilo responsivo da tela de edição. |
| `mysite/apps/calendarios/templates/calendarios/calendario.html` | Exibe a confirmação depois do redirecionamento. |
| `mysite/apps/calendarios/tests.py` | Testes de GET, atualização, validação e autorização. |
| `doc/cdu/010/cdu_010.md` | Link para este guia. |

Não é necessária uma migração: os campos `nome` e `descricao` já existem no
modelo `Calendario`, com limites de 100 e 500 caracteres, respectivamente.

## Fluxo implementado

1. A ação “Editar calendário” na página do calendário abre a rota
   `/calendarios/atualizar_calendario/<id>` com GET.
2. A view busca o calendário; retorna 404 se o identificador não existir.
3. A view confere no servidor se o usuário tem um vínculo administrador.
   Usuários sem vínculo ou sem papel de administrador recebem HTTP 403, tanto
   no GET quanto no POST.
4. O formulário mostra os valores atuais. “Cancelar” é um link de volta para
   o calendário e não envia nem salva dados.
5. No POST, o `ModelForm` valida obrigatoriedade e comprimentos. Em caso de
   erro, a mesma tela é renderizada com os valores enviados e as mensagens de
   validação.
6. Com dados válidos, o formulário salva os campos, mostra uma mensagem de
   sucesso na página seguinte e redireciona para o calendário atualizado.

## Código principal

### Formulário

`ModelForm` reaproveita os campos e regras já declarados no modelo. Assim, os
limites do banco e do formulário permanecem alinhados.

```python
from django import forms

from apps.calendarios.models import Calendario


class CalendarioForm(forms.ModelForm):
    class Meta:
        model = Calendario
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'off'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }
```

### View

`@login_required` exige autenticação; `@require_http_methods` limita o endpoint
a GET e POST. A autorização é repetida na view para que não dependa de o botão
estar ou não visível na interface.

```python
@login_required
@require_http_methods(['GET', 'POST'])
def atualizar_calendario(request, id):
    calendario = get_object_or_404(Calendario, id=id)
    membro = MembroDeCalendario.objects.filter(
        usuario=request.user,
        calendario=calendario,
    ).first()

    if not membro or not membro.eh_admin:
        return HttpResponseForbidden(
            'Somente administradores podem atualizar este calendário.'
        )

    dados = request.POST if request.method == 'POST' else None
    form = CalendarioForm(dados, instance=calendario)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Calendário atualizado com sucesso.')
        return redirect('calendario', id=id)

    return render(
        request,
        'calendarios/atualizar_calendario.html',
        {
            'calendario': calendario,
            'form': form,
            'paleta': membro.numero_paleta,
        },
    )
```

`dados` é definido como `request.POST` em qualquer POST, inclusive se o
formulário vier vazio. Isso é importante para que o Django valide os campos
obrigatórios em vez de tratar o formulário como não enviado.

### Template

O formulário inclui token CSRF, erros por campo e controles que funcionam sem
JavaScript. Os atributos `maxlength` e `required` são gerados pelo formulário
com base na definição do modelo; a validação do servidor continua sendo a
autoridade.

```django
<form method="post">
    {% csrf_token %}
    {% for field in form %}
        <div class="formulario-calendario__campo">
            <label for="{{ field.id_for_label }}">{{ field.label }}</label>
            {{ field }}
            {% if field.errors %}
                <ul class="formulario-calendario__erros" role="alert">
                    {% for error in field.errors %}
                        <li>{{ error }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        </div>
    {% endfor %}

    <div class="formulario-calendario__acoes">
        <a href="{% url 'calendario' calendario.id %}">Cancelar</a>
        <button type="submit">Salvar alterações</button>
    </div>
</form>
```

A página do calendário também percorre o contexto `messages` para mostrar
“Calendário atualizado com sucesso.” após o redirecionamento.

## Como reproduzir a implementação

1. No app `calendarios`, crie `forms.py` com o `CalendarioForm` acima.
2. Importe o formulário e os utilitários do Django em `views.py`; substitua o
   placeholder da view `atualizar_calendario` pela implementação acima.
3. Crie `templates/calendarios/atualizar_calendario.html`, estenda
   `core/base.html`, carregue o CSS do app e adicione os campos, erros, token
   CSRF, botão de salvar e link de cancelamento.
4. Crie `static/calendarios/css/atualizar_calendario.css` para estilizar a
   tela; o comportamento do formulário não depende desse arquivo.
5. Em `calendario.html`, apresente as mensagens flash para que o usuário veja
   a confirmação ao voltar à visualização.
6. Preserve a rota existente `atualizar_calendario/<int:id>` em
   `apps/calendarios/urls.py`; a tela já é alcançada pela ação “Editar
   calendário” dos usuários administradores.
7. Execute os testes a partir do diretório `mysite`:

   ```bash
   python manage.py test apps.calendarios.tests --settings=config.settings.testing
   ```

## Testes cobertos

- GET de administrador exibe dados atuais, botão de cancelar e token CSRF.
- POST válido atualiza os campos e redireciona com confirmação.
- POST com campos acima dos limites mantém os dados enviados e não altera o
  calendário no banco.
- Nome vazio é rejeitado sem salvar.
- POST vazio é tratado como envio e retorna erros de validação.
- Membro comum não consegue enviar alterações.
- Usuário sem vínculo não consegue abrir a tela de edição.

Para validar manualmente, entre com uma conta administradora, abra um
calendário e selecione o ícone de edição. Teste salvar valores válidos,
ultrapassar os limites dos campos e cancelar antes do envio. Repita o acesso
com um membro comum e confirme que a requisição é recusada.
