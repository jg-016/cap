# Implementação do CDU-024 — Remover participante de turma

Este documento descreve como reproduzir a implementação do CDU-024 no CAP: alterações de interface, autorização no servidor, remoção dos vínculos, migração dos dados antigos, testes e comandos de validação.

O documento funcional com fluxos alternativos está em [cdu_024_completo.md](./cdu_024_completo.md). Os arquivos citados abaixo são a fonte definitiva do código; os trechos neste guia destacam a lógica necessária para reconstruir o mesmo comportamento.

## 1. Comportamento entregue

Um estudante administrador pode remover um participante comum pela aba **Membros** da página da turma. Antes da alteração, a interface pede confirmação e identifica o participante. A confirmação envia um `POST` com CSRF; no servidor, a autorização e as condições da remoção são verificadas novamente.

Quando a remoção é aceita:

1. O vínculo `MembroDeTurma` do participante com a turma é apagado.
2. Na mesma transação, são apagados os vínculos `MembroDeCalendario` desse participante com calendários associados àquela turma.
3. Os calendários, seus eventos, a conta do participante, os vínculos com calendários pessoais e os vínculos com outras turmas permanecem intactos.

O sistema não oferece a remoção do próprio administrador nem de outro administrador. Uma requisição direta com esses alvos também é negada no servidor.

### Fluxo de ponta a ponta

1. Um administrador abre a aba **Membros** da turma e escolhe remover um participante comum.
2. A interface identifica o participante no diálogo de confirmação; confirmar envia um formulário `POST` com CSRF para a rota de remoção.
3. A view exige autenticação e método `POST`, valida no servidor o papel de administrador, a participação do alvo e as regras contra auto-remoção ou remoção de outro administrador.
4. Em uma transação, remove o vínculo com a turma e os vínculos do participante com calendários daquela turma; não apaga calendários, eventos, conta ou vínculos fora da turma.
5. Em caso de sucesso, mostra uma confirmação e redireciona à turma. O participante removido não consegue voltar à página da turma por URL direta.

## 2. Modelo e regra de autorização

Os papéis são registrados nos vínculos, e não inferidos a partir do tipo de conta Django:

- `MembroDeTurma.eh_admin` define a administração da turma.
- `MembroDeCalendario.eh_admin` define a administração de um calendário.

O uso de `create_superuser()` para gerar contas de desenvolvimento não substitui essas permissões do domínio. A página e as operações administrativas da turma dependem de `MembroDeTurma.eh_admin`.

Uma consequência importante é que uma pessoa pode ser administradora de um calendário sem estar marcada como administradora da turma que o contém. A seção 8 explica a correção dos dados legados e a regra usada no `populate`.

## 3. Arquivos alterados e criados

### Documentação funcional

- [cdu_024_completo.md](./cdu_024_completo.md) — fluxo principal, fluxos alternativos, pré/pós-condições e regras de autorização.
- [diagramas_cdu_024.md](./diagramas_cdu_024.md) — diagramas relacionados ao caso de uso.

### Implementação

| Arquivo | Alteração relacionada |
| --- | --- |
| [views.py](../../../mysite/apps/turmas/views.py) | Contexto de autorização da página, sincronização de participantes dos calendários e view `remover_participante_turma`. |
| [urls.py](../../../mysite/apps/turmas/urls.py) | Rota POST nomeada `remover_participante_turma` e alias de compatibilidade. |
| [utils.py](../../../mysite/apps/turmas/utils.py) | Inclusão de `usuario_id` nos dados usados para renderizar as ações por participante. |
| [painel_membros.html](../../../mysite/apps/core/templates/core/painel_membros.html) | Lista única de membros, botão e diálogo de confirmação apenas para membros comuns. |
| [modal_participante_turma.js](../../../mysite/apps/turmas/static/turmas/js/modal_participante_turma.js) | Abertura/fechamento dos diálogos e fechamento ao clicar fora deles. **Arquivo criado.** |
| [painel_membros.css](../../../mysite/apps/core/static/core/css/painel_membros.css) | Estilos responsivos da lista de membros e do diálogo de remoção. |
| [turma.html](../../../mysite/apps/turmas/templates/turmas/turma.html) | Carregamento do JavaScript da remoção e composição da tela da turma. |
| [calendario_geral.py](../../../mysite/apps/core/views/calendario_geral.py) | Ignora, ao compor eventos, calendários para os quais o usuário não tem vínculo, em vez de lançar `DoesNotExist`. |
| [populate.py](../../../mysite/apps/core/management/commands/populate.py) | Atribui papel de administrador da turma de forma consistente com os calendários sem eliminar membros comuns. |
| [0004_promover_admins_dos_calendarios.py](../../../mysite/apps/turmas/migrations/0004_promover_admins_dos_calendarios.py) | Promove os administradores de calendários associados a administradores das turmas legadas. **Arquivo criado.** |
| [tests.py — core](../../../mysite/apps/core/tests.py) | Teste integrado da população, dos papéis e da renderização das ações administrativas. |
| [tests.py — turmas](../../../mysite/apps/turmas/tests.py) | Testes de migração, interface, autorização e efeitos da remoção. |
| [calendarios_turma.css](../../../mysite/apps/turmas/static/turmas/css/calendarios_turma.css) | Estilo da seção administrativa de calendários; lista em coluna única e layout responsivo. |

As ações de criar, associar e remover calendários da página da turma são funcionalidades auxiliares já integradas à mesma interface administrativa. O endpoint `remover_calendario_turma` apaga o calendário e seus eventos; essa operação não é a remoção de participante do CDU-024.

## 4. Preparação dos dados apresentados à interface

`obter_dados_turma()` já separava os membros entre `lideres` e `colegas`. Para construir URLs e identificar o participante no botão, cada item precisa conter o ID do usuário:

```python
dados_membro = {
    'usuario_id': usuario.id,
    'nome': usuario.nome_completo,
    'email': usuario.email,
}

if membro.eh_admin:
    dados_membros['lideres'].append(dados_membro)
else:
    dados_membros['colegas'].append(dados_membro)
```

O trecho está em [utils.py](../../../mysite/apps/turmas/utils.py). A separação dos papéis é usada pelo template para nunca apresentar a ação de remoção a um administrador como alvo.

Na view `turma()`, a permissão é calculada a partir do vínculo da pessoa autenticada com a turma:

```python
membro_turma = get_object_or_404(
    MembroDeTurma,
    usuario=request.user,
    turma=turma,
)
membro = membro_turma.eh_admin

context = {
    'turma': dados_turma,
    'painel_membros': dados_membros,
    'usuario_eh_admin': membro,
    'pode_remover_participantes': membro,
    # Demais dados já usados pelo template.
}
```

O contexto controla a aba **Calendários**, as ferramentas administrativas da turma e a exibição dos botões de remoção. A view também exige que o usuário tenha vínculo ativo com a turma; um usuário removido ou não participante recebe 404 ao acessar a página diretamente. Para operações que alteram dados, a view específica ainda verifica a permissão de administrador no servidor.

## 5. Interface de membros e confirmação

O parcial [painel_membros.html](../../../mysite/apps/core/templates/core/painel_membros.html) renderiza uma lista única. Para cada colega, botão e diálogo são condicionados a `pode_remover_participantes` e ao fato de o alvo não ser o próprio usuário:

```django
{% for membro in painel_membros.colegas %}
    <li class="membro">
        <div class="membro__identidade">
            <span class="icone-email material-symbols-outlined">mail</span>
            <p class="nome-membro">{{ membro.nome }}</p>
        </div>
        {% if pode_remover_participantes and membro.usuario_id != request.user.id %}
            <button
                type="button"
                class="membro__acao"
                data-abrir-modal="modal-remover-participante-{{ membro.usuario_id }}"
                aria-label="Remover participante {{ membro.nome }}"
            >
                Remover
            </button>
        {% endif %}
    </li>
    {% if pode_remover_participantes and membro.usuario_id != request.user.id %}
        <dialog
            class="modal-remover-participante"
            id="modal-remover-participante-{{ membro.usuario_id }}"
        >
            <section class="modal-remover-participante__conteudo">
                <button
                    type="button"
                    class="modal-remover-participante__fechar"
                    data-fechar-modal
                    aria-label="Fechar"
                >&times;</button>
                <h3>Remover participante?</h3>
                <p>
                    Deseja remover <strong>{{ membro.nome }}</strong> da turma?
                    O acesso dele aos calendários associados será revogado.
                </p>
                <form
                    method="post"
                    action="{% url 'remover_participante_turma' turma.id membro.usuario_id %}"
                >
                    {% csrf_token %}
                    <div class="modal-remover-participante__acoes">
                        <button type="button" data-fechar-modal>Cancelar</button>
                        <button type="submit" class="modal-remover-participante__confirmar">
                            Remover
                        </button>
                    </div>
                </form>
            </section>
        </dialog>
    {% endif %}
{% endfor %}
```

O formulário não faz alterações ao abrir ou cancelar o diálogo. A alteração só ocorre no envio do formulário. `{% csrf_token %}` protege o `POST`; `data-abrir-modal` e `data-fechar-modal` conectam os controles ao JavaScript.

### JavaScript dos diálogos

O arquivo novo [modal_participante_turma.js](../../../mysite/apps/turmas/static/turmas/js/modal_participante_turma.js) delega os cliques ao documento e limita os seletores ao painel de membros:

```javascript
document.addEventListener('click', (event) => {
    const openButton = event.target.closest('#painel-membros [data-abrir-modal]');
    if (openButton) {
        document.getElementById(openButton.dataset.abrirModal)?.showModal();
        return;
    }

    const closeButton = event.target.closest('#painel-membros [data-fechar-modal]');
    if (closeButton) {
        closeButton.closest('dialog')?.close();
        return;
    }

    if (event.target instanceof HTMLDialogElement && event.target.open) {
        const bounds = event.target.getBoundingClientRect();
        const clickedBackdrop = event.clientX < bounds.left
            || event.clientX > bounds.right
            || event.clientY < bounds.top
            || event.clientY > bounds.bottom;

        if (clickedBackdrop) {
            event.target.close();
        }
    }
});
```

O script é carregado com `defer` em [turma.html](../../../mysite/apps/turmas/templates/turmas/turma.html). A remoção não é adicionada ao template da página de calendário; isso mantém a ação no contexto do CDU-024, que é a turma.

### CSS da lista e do diálogo

O estilo está em [painel_membros.css](../../../mysite/apps/core/static/core/css/painel_membros.css). Ele usa as variáveis visuais do projeto (`--cor-borda`, `--raio`, `--cor-de-fundo-*`, `--sombra-modal`), organiza cada participante em linha flexível e adapta o diálogo em telas estreitas.

Os seletores centrais são:

```css
.lista-membros {
    list-style: none;
    padding: 0;
    margin: 0;
    border: 1px solid var(--cor-borda);
    border-radius: var(--raio);
    overflow: hidden;
    background: var(--cor-de-fundo-1);
}

.membro {
    min-height: 56px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--cor-borda);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.membro__acao {
    border: 1px solid transparent;
    border-radius: var(--raio);
    background: transparent;
    color: #8a2525;
    font: inherit;
    padding: 6px 10px;
    cursor: pointer;
    white-space: nowrap;
}

.modal-remover-participante {
    box-sizing: border-box;
    width: min(420px, calc(100% - 32px));
    padding: 0;
    margin: auto;
    border: 0;
    border-radius: var(--raio-modal);
    box-shadow: var(--sombra-modal);
}

.modal-remover-participante::backdrop {
    background: rgba(17, 24, 39, 0.6);
}
```

O CSS completo também estiliza ícones, estados de hover, botões de confirmação e o layout responsivo; consulte o arquivo linkado para os valores integrais.

## 6. Rota e validação no servidor

A URL nomeada usada pelo formulário é registrada em [urls.py](../../../mysite/apps/turmas/urls.py):

```python
path(
    'remover_participante/<int:turma_id>/<int:usuario_id>',
    views.remover_participante_turma,
    name='remover_participante_turma',
),
```

Há também uma rota de compatibilidade `remover_participante_turma/<int:turma_id>/<int:usuario_id>`, nomeada `remover_participante_turma_legacy`.

A view no arquivo [views.py](../../../mysite/apps/turmas/views.py) é a autoridade final:

```python
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
        messages.error(
            request,
            'Você não tem permissão para remover participantes desta turma.',
        )
        return redirect('turma', turma.id)

    if request.user.id == usuario_id:
        messages.error(
            request,
            'Você não pode remover a si mesmo da turma. Use a opção de sair da turma.',
        )
        return redirect('turma', turma.id)

    membro = get_object_or_404(
        MembroDeTurma,
        turma=turma,
        usuario_id=usuario_id,
    )

    if membro.eh_admin:
        messages.error(
            request,
            'Administradores não podem remover outros administradores da turma.',
        )
        return redirect('turma', turma.id)

    with transaction.atomic():
        membro.delete()
        MembroDeCalendario.objects.filter(
            usuario_id=usuario_id,
            calendario__turma=turma,
        ).delete()

    messages.success(
        request,
        f'{membro.usuario.nome_completo} foi removido da turma.',
    )
    return redirect('turma', turma.id)
```

### Por que cada validação existe

1. `@login_required`: exige uma sessão autenticada.
2. `@require_POST`: impede que abrir um link GET altere o estado.
3. `get_object_or_404(Turma, ...)`: retorna 404 se a turma não existe.
4. A consulta do administrador confere `eh_admin=True` no vínculo **dessa** turma, sem confiar em dados enviados pelo navegador.
5. A verificação de `request.user.id` proíbe auto-remoção.
6. `get_object_or_404(MembroDeTurma, turma=..., usuario_id=...)` confirma que o alvo pertence à turma.
7. `membro.eh_admin` proíbe remover outro administrador.
8. `transaction.atomic()` agrupa os dois deletes: se um falhar, o banco não deve deixar o estado parcialmente removido.
9. O filtro dos vínculos de calendário usa `calendario__turma=turma`, portanto não apaga calendários pessoais nem vínculos do participante com outras turmas.
10. A mensagem de sucesso é criada somente depois da transação e o usuário volta à página da turma.

Erros de recurso inexistente são tratados por 404; tentativas sem permissão ou com alvos proibidos recebem mensagem e redirecionamento sem apagar vínculos.

## 7. Integração com o calendário da turma

A view `turma()` monta o calendário geral com `turma.calendarios.all()`. Depois de uma remoção, o contexto não pode presumir que todo usuário ainda tem vínculo com todo calendário do queryset.

Em [calendario_geral.py](../../../mysite/apps/core/views/calendario_geral.py), a obtenção do vínculo foi alterada de `.get()` para `.filter(...).first()`. Se o vínculo não existe, o calendário é ignorado ao gerar os eventos:

```python
membro_calendario = MembroDeCalendario.objects.filter(
    calendario=calendario,
    usuario=request.user,
).first()

if membro_calendario is None:
    continue
```

Isso evita uma exceção `DoesNotExist` e não concede acesso: sem vínculo, não são incluídos eventos daquele calendário no contexto.

O helper `_sincronizar_membros_calendario_turma()` em [views.py](../../../mysite/apps/turmas/views.py) cria os vínculos de calendário que faltarem para os participantes atuais da turma. Para vínculos já existentes, preserva a permissão e atualiza somente a paleta quando necessário:

```python
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
```

Na mesma seção administrativa existem as operações auxiliares para calendários:

- `adicionar_calendario_turma`: exige administrador da turma; valida o calendário escolhido, exige que seja pessoal e acessível ao ator, associa-o à turma e sincroniza os participantes.
- `criar_calendario_turma`: exige administrador; cria o calendário diretamente associado à turma e sincroniza seus participantes.
- `remover_calendario_turma`: exige administrador; confirma que o calendário pertence à turma indicada e apaga o calendário.

Essas ações são chamadas por formulários POST com CSRF e possuem modais no template. O arquivo [calendarios_turma.css](../../../mysite/apps/turmas/static/turmas/css/calendarios_turma.css) mantém a lista de calendários em uma coluna (`grid-template-columns: minmax(0, 1fr)`) e aplica o estilo responsivo da seção.

A remoção de participante e a remoção de calendário têm efeitos diferentes:

- Remover **participante** apaga somente os vínculos desse usuário; preserva o calendário e eventos para as outras pessoas.
- Remover **calendário** usa `calendario.delete()` e, devido às relações do modelo, apaga aquele calendário e seus eventos.

## 8. Administradores nas turmas antigas e no `populate`

### Causa do problema

As páginas só mostram a aba **Calendários** e as ações administrativas quando `MembroDeTurma.eh_admin` é verdadeiro. Nos dados antigos, alguns usuários eram administradores dos calendários da turma (`MembroDeCalendario.eh_admin=True`), mas continuavam membros comuns da turma. A página os tratava como alunos e escondia a aba e as ações.

### Migração de dados

Foi criado [0004_promover_admins_dos_calendarios.py](../../../mysite/apps/turmas/migrations/0004_promover_admins_dos_calendarios.py). A migração percorre os vínculos de administrador de calendários que têm uma turma associada e promove o vínculo correspondente da mesma pessoa com a turma. O arquivo completo é:

```python
from django.db import migrations


def promover_admins_dos_calendarios(apps, schema_editor):
    MembroDeCalendario = apps.get_model('calendarios', 'MembroDeCalendario')
    MembroDeTurma = apps.get_model('turmas', 'MembroDeTurma')
    database = schema_editor.connection.alias

    administradores = MembroDeCalendario.objects.using(database).filter(
        eh_admin=True,
        calendario__turma__isnull=False,
    ).values_list('usuario_id', 'calendario__turma_id').distinct()

    for usuario_id, turma_id in administradores.iterator():
        MembroDeTurma.objects.using(database).filter(
            usuario_id=usuario_id,
            turma_id=turma_id,
        ).update(eh_admin=True)


class Migration(migrations.Migration):

    dependencies = [
        ('calendarios', '0003_initial'),
        ('turmas', '0003_alter_turma_codigo'),
    ]

    operations = [
        migrations.RunPython(promover_admins_dos_calendarios, migrations.RunPython.noop),
    ]
```

A migração:

- não cria nem remove turmas, calendários, eventos ou contas;
- não promove membros comuns de calendários;
- não usa membros de calendários pessoais para promover alguém;
- não redefine papéis já verdadeiros;
- usa `RunPython.noop` no rollback para não rebaixar silenciosamente administradores promovidos.

### Novos dados de desenvolvimento

Em [populate.py](../../../mysite/apps/core/management/commands/populate.py), `popular_turmas()` constrói `administradores_ids` a partir dos membros que são administradores dos calendários recém-associados. Esses usuários recebem `eh_admin=True` na turma, e os demais continuam membros comuns. Se uma turma não tiver calendários nem administradores encontrados, o primeiro usuário é usado como fallback para manter uma conta administrativa de desenvolvimento.

Essa regra depende da ordem de criação: primeiro a turma é criada, depois `popular_calendarios()` cria seus calendários e respectivos registros `MembroDeCalendario`; só então `popular_turmas()` consulta esses registros para decidir quem será administrador da turma. Se a ordem for invertida, a consulta não encontra administradores e o fallback é usado.

```python
def popular_turmas(dados_turmas):
    usuarios = list(Usuario.objects.order_by('id'))

    for dados in dados_turmas:
        dados_calendarios = dados.pop('calendarios', [])
        numero_paleta = dados.pop('numero_paleta', 1)
        descricao = f'Bem vindo a {dados['nome']}!'

        turma = Turma.objects.create(descricao=descricao, **dados)
        popular_calendarios(
            dados_calendarios,
            turma=turma,
            numero_paleta=numero_paleta,
        )

        administradores_ids = set(
            MembroDeCalendario.objects.filter(
                calendario__turma=turma,
                eh_admin=True,
            ).values_list('usuario_id', flat=True)
        )
        if not administradores_ids and usuarios:
            administradores_ids.add(usuarios[0].id)

        for usuario in usuarios:
            MembroDeTurma.objects.create(
                usuario=usuario,
                turma=turma,
                eh_admin=usuario.id in administradores_ids,
                numero_paleta=numero_paleta,
            )
```

O `populate` continua sendo um comando destrutivo que recria o banco de desenvolvimento. Não é necessário executá-lo para corrigir o banco existente: a correção dos dados antigos é feita pela migração.

## 9. Testes

### Testes específicos do CDU-024

Em [turmas/tests.py](../../../mysite/apps/turmas/tests.py):

- `test_promove_admin_de_calendario_sem_promover_membros_comuns` — executa a migração de dados a partir do estado anterior e verifica que o administrador de calendário vira administrador da turma, enquanto o membro comum continua comum.
- `test_administrador_remove_membro_e_revoga_acesso_ao_calendario_da_turma` — verifica a remoção do vínculo com a turma e com os calendários associados, preservando o calendário pessoal.
- `test_membro_removido_nao_acessa_mais_a_pagina_da_turma` — depois da remoção, confirma que o usuário não participante recebe 404 ao tentar acessar a página da turma.
- `test_administrador_nao_pode_remover_a_si_mesmo` — confirma que o vínculo do ator é mantido e uma mensagem de erro é apresentada.
- `test_administrador_nao_pode_remover_outro_administrador` — confirma que o alvo administrador permanece na turma.
- `test_membro_comum_nao_pode_remover_participante` — confirma que um não administrador não remove ninguém.
- `test_pagina_da_turma_exibe_botoes_de_remocao_para_administradores` — confere a aba de membros, a lista única, o botão e o diálogo, sem oferecer remoção do próprio administrador.
- `test_participante_nao_ve_botoes_de_remocao` — verifica que o membro comum não recebe a ação na interface.
- `test_pagina_de_calendario_nao_exibe_opcao_de_remover_participante` — garante que a ação não aparece na página do calendário.

Em [core/tests.py](../../../mysite/apps/core/tests.py):

- `test_admins_dos_calendarios_da_turma_recebem_acesso_as_acoes_da_turma` — popula uma turma com administradores de calendário e membro comum; verifica os papéis, a aba Calendários, as ações de associar/criar/remover calendário e a remoção de membro.

### Testes de funções administrativas de turma executados junto ao conjunto

O arquivo [turmas/tests.py](../../../mysite/apps/turmas/tests.py) também verifica atualização da turma, sincronização de paletas, associação e criação de calendários, e as rotas de remoção de calendário:

- `test_atualizar_turma_altera_nome_e_descricao`
- `test_atualizar_turma_sincroniza_apenas_paleta_do_usuario`
- `test_paleta_invalida_impede_atualizar_turma`
- `test_membro_comum_nao_pode_atualizar_turma`
- `test_get_atualizar_turma_redireciona_para_detalhes`
- `test_pagina_da_turma_exibe_modal_para_administrador`
- `test_nome_vazio_nao_atualiza_turma_e_exibe_erro`
- `test_associar_calendario_existente_sincroniza_paletas_e_preserva_permissoes`
- `test_criar_calendario_para_turma_cria_vinculos_dos_membros`
- `test_remover_calendario_desvincula_sem_exclui_lo`
- `test_rota_generica_remove_calendario_informado_no_post`

### Comando e resultado da validação

No diretório `mysite`, o conjunto foi executado com:

```bash
python manage.py test apps.core.tests apps.turmas.tests
```

Resultado obtido nesta revisão: **21 testes passaram**, com `System check identified no issues`.

As alterações também foram verificadas com:

```bash
python manage.py makemigrations --check --dry-run
git diff --check
```

Não foram detectadas alterações de modelo sem migração nem erros de whitespace. A migração foi aplicada ao banco de desenvolvimento do workspace:

```bash
python manage.py migrate turmas 0004_promover_admins_dos_calendarios
```

Depois disso, a renderização das páginas Infoweb 3M e Infoweb 2V foi verificada com administradores autenticados: resposta HTTP 200 e presença da aba Calendários, das ações de associar/criar/remover calendários e de remover membros.

## 10. Como reproduzir a implementação em outro ambiente

1. **Verifique os modelos**: confirme que `MembroDeTurma` e `MembroDeCalendario` possuem `usuario`, `turma`/`calendario` e `eh_admin`.
2. **Inclua o identificador do membro no contexto**: adicione `usuario_id` ao dicionário que alimenta a lista.
3. **Exija participação antes de montar a página**: busque `MembroDeTurma` por usuário e turma com `get_object_or_404`, para retornar 404 quando o vínculo não existe; depois derive `usuario_eh_admin` de `membro_turma.eh_admin`. Use essa permissão para renderizar ações, mas não como única validação.
4. **Implemente a lista e o diálogo**: o botão deve existir apenas para administradores e membros comuns; o formulário deve usar POST, CSRF e enviar IDs como parâmetros da URL.
5. **Registre uma URL nomeada** para o endpoint de remoção.
6. **Implemente a view protegida** com `login_required` e `require_POST`. Valide administrador, alvo na turma, auto-remoção e alvo não administrador.
7. **Apague ambos os vínculos em uma transação**: o vínculo da turma e os vínculos do alvo apenas com calendários daquela turma.
8. **Não apague recursos compartilhados** na remoção do participante; preserve calendários, eventos e associações não relacionadas.
9. **Trate o calendário geral** sem presumir que todos os calendários consultados ainda têm vínculo com o usuário.
10. **Corrija os dados legados** com uma migração de dados que alinhe os administradores de calendários associados à turma com o papel administrativo da turma.
11. **Atualize o `populate`** para criar pelo menos uma turma com administradores e membros comuns, facilitando a validação manual.
12. **Adicione testes** de sucesso, autorização, auto-remoção, proteção de administradores, escopo dos vínculos apagados, UI e migração de dados.
13. **Execute migrações e testes** antes de disponibilizar a mudança.

Seguindo estes passos e preservando os trechos referenciados, a implementação mantém a autorização no servidor, a confirmação segura e a semântica de dados definida no CDU-024.

## 11. Sequência de execução e invariantes

### Fluxo de sucesso

1. O navegador solicita `GET` da turma.
2. `turma()` busca a entidade e o vínculo `MembroDeTurma` do usuário; se o vínculo não existe, retorna 404. O papel administrativo é derivado de `membro_turma.eh_admin`.
3. `obter_dados_turma()` prepara os nomes, IDs e grupos de membros; o template renderiza a aba **Membros**.
4. O administrador seleciona **Remover** ao lado de um colega. O JavaScript abre o `<dialog>` identificado pelo ID daquele usuário.
5. **Cancelar**, fechar o diálogo ou clicar no backdrop apenas fecha o modal; nenhum formulário é enviado.
6. **Remover** envia `POST /turmas/remover_participante/<turma_id>/<usuario_id>` com token CSRF.
7. Os decorators exigem login e método POST. A view busca a turma, valida o vínculo administrativo do ator, valida o alvo e rejeita auto-remoção ou alvo administrador.
8. A transação apaga o vínculo de turma e os vínculos do alvo com calendários cujo `calendario.turma` é a turma recebida.
9. A view grava a mensagem de sucesso e redireciona à página da turma.
10. A nova renderização consulta os vínculos atualizados; o membro removido não aparece mais na lista.

### Invariantes que a implementação deve preservar

| Situação | Resultado esperado |
| --- | --- |
| Administrador remove membro comum | Remove os dois tipos de vínculo dentro da mesma transação. |
| Membro comum tenta remover alguém | Não altera nenhum vínculo; recebe erro de permissão. |
| Administrador tenta remover a si mesmo | Não altera os vínculos; recebe orientação para usar o fluxo de saída da turma. |
| Administrador tenta remover outro administrador | Não altera os vínculos; recebe erro. |
| Usuário não pertence a um calendário pessoal | Esse vínculo pessoal não deve ser apagado pela remoção da turma. |
| Calendário pertence a outra turma | Seus vínculos não são selecionados pelo filtro de remoção. |
| Calendário usado por outros participantes | O calendário e seus eventos continuam existentes. |
| Turma ou vínculo de alvo não existe | A view retorna 404 via `get_object_or_404`; nenhuma exclusão ocorre. |
| Requisição GET para a URL de remoção | O decorator `require_POST` impede que a exclusão seja executada. |

O filtro `calendario__turma=turma` é parte essencial do escopo: não o substitua por um delete de todos os `MembroDeCalendario` do usuário, pois isso também removeria calendários pessoais e associações não relacionadas.

## 12. Validação manual no navegador

Os testes Django validam a resposta HTTP, a presença dos elementos renderizados, a autorização e o estado persistido no banco. Eles não executam um navegador real; portanto, a interação visual do `<dialog>` e o JavaScript devem ser conferidos manualmente:

1. Aplique as migrações em um ambiente de desenvolvimento: `python manage.py migrate`.
2. Garanta que a turma tenha pelo menos um `MembroDeTurma` administrador, um membro comum e um calendário associado com vínculos de calendário.
3. Entre com o administrador e abra a página da turma.
4. Abra **Membros** e confirme que há botão **Remover** para o membro comum, mas não para si próprio nem para administradores.
5. Abra a confirmação e confira o nome do alvo e o aviso sobre acesso aos calendários.
6. Selecione **Cancelar**, feche pelo botão `×` e clique fora do diálogo; em todos os casos, confirme que a pessoa continua membro.
7. Abra novamente, confirme **Remover** e verifique a mensagem de sucesso e a ausência do participante na lista.
8. Entre com o usuário removido e tente abrir diretamente a URL da turma; o resultado esperado é 404, sem erro interno nem acesso aos dados.
9. Confira no banco que os vínculos `MembroDeTurma` e `MembroDeCalendario` daquela turma foram removidos, mas a conta, os calendários/eventos e vínculos pessoais ou de outras turmas permaneceram.
10. Entre como membro comum e envie manualmente um `POST` para a rota de remoção: a view deve negar a operação sem alterar dados.
11. Repita as tentativas contra o próprio administrador e outro administrador; ambos devem permanecer na turma.

Para inspecionar rapidamente o HTML sem navegador, use o `Client` do Django nos testes ou as verificações de `assertContains` em [turmas/tests.py](../../../mysite/apps/turmas/tests.py). Isso verifica a renderização no servidor, mas não substitui os passos de interação do modal.

## 13. Observações de manutenção

- A migração usa `apps.get_model()` para consultar os modelos históricos do estado da migração. Não importe os modelos atuais de `apps.turmas.models` ou `apps.calendarios.models` dentro dela.
- O critério de promoção é “administrador de ao menos um calendário associado à turma”. Se a regra de negócio mudar para exigir administração em todos os calendários, altere a migração/população conforme a política aprovada e ajuste os testes; não mude apenas a condição do template.
- A migração é de dados e não exige alteração do esquema. O comando `makemigrations --check --dry-run` deve continuar informando `No changes detected`.
- A página da turma exige um vínculo `MembroDeTurma` existente. Use `get_object_or_404(MembroDeTurma, usuario=request.user, turma=turma)` antes de chamar `obter_dados_turma()`; caso contrário, um usuário removido pode produzir contexto vazio e falha ao acessar `dados_turma.pop('membros')`.
- Não rode `populate` para corrigir dados em ambientes com dados que devem ser preservados: o comando apaga o banco de desenvolvimento antes de recriá-lo. Use a migração `0004_promover_admins_dos_calendarios`.
- O alias de URL `remover_participante_turma_legacy` é uma compatibilidade de rota. Formulários novos devem usar a URL nomeada `remover_participante_turma`.
- A remoção de calendário é distinta da remoção de participante: confirme a cópia do modal e a política do CDU-011 antes de alterar o `calendario.delete()` usado por essa outra operação.

