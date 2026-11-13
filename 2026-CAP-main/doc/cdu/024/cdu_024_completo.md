# CDU-024 Remover participante de turma

- **Ator principal**: Estudante administrador da turma
- **Atores secundários**: Nenhum
- **Descrição**: Um estudante administrador remove outro participante da turma.
- **Pré-condição**: O ator está autenticado, é administrador da turma e o participante selecionado está associado a ela.
- **Pós-Condição**: O participante deixa de estar associado à turma e perde o acesso aos calendários associados a ela. Os calendários e seus eventos permanecem disponíveis para os demais participantes.

## Fluxo Principal

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 1. O estudante administrador acessa a página da turma e abre a aba “Membros”. | 2. O sistema verifica a participação e a permissão do ator, e exibe os participantes e as ações administrativas disponíveis. |
| 3. O ator seleciona “Remover” para outro participante. | 4. O sistema apresenta uma confirmação com o nome do participante e informa que ele perderá o acesso à turma e aos calendários associados. |
| 5. O ator confirma a remoção. | 6. O sistema recebe a solicitação autenticada de remoção e verifica novamente a permissão de administrador. |
|  | 7. O sistema confirma que o participante pertence à turma e que o alvo não é o próprio ator. |
|  | 8. O sistema remove, em uma única operação, o vínculo do participante com a turma e os vínculos dele com os calendários associados à turma. |
|  | 9. O sistema mantém os calendários e eventos da turma, registra a confirmação e redireciona o ator para a página da turma. |
| 10. O ator consulta a lista atualizada de participantes. | 11. O sistema exibe a turma sem o participante removido e apresenta uma mensagem de sucesso. |

## Fluxo Alternativo I — Ator cancela a remoção

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 3.1. O ator seleciona “Cancelar” na confirmação. | 3.2. O sistema fecha a confirmação e retorna à lista de participantes, sem alterar os vínculos. |

## Fluxo Alternativo II — Ator sem permissão

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 1.1. Um estudante que não administra a turma tenta acessar a ação ou enviar uma solicitação de remoção. | 1.2. O sistema verifica a permissão no servidor e identifica que o ator não é administrador da turma. |
|  | 1.3. O sistema nega a operação, informa a falta de permissão e mantém os vínculos inalterados. |

## Fluxo Alternativo III — Participante ou turma inexistente

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 5.1. A solicitação contém uma turma inexistente ou um participante que não pertence à turma. | 5.2. O sistema não encontra o recurso ou o vínculo informado, não altera os dados e responde com erro de recurso não encontrado. |

## Fluxo Alternativo IV — Ator tenta remover a si mesmo

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 5.3. O ator envia uma solicitação para remover o próprio vínculo. | 5.4. O sistema nega a operação por este caso de uso e mantém a participação. Para sair da turma, o estudante deve utilizar o CDU-027 — Sair de turma. |

## Fluxo Alternativo V — Ator tenta remover outro administrador

| Ações do ator | Ações do sistema |
| :--- | :--- |
| 5.5. O administrador envia uma solicitação para remover outro administrador da turma. | 5.6. O sistema nega a operação e mantém os vínculos inalterados. |

## Regras e observações

- A permissão deve ser conferida no servidor no momento da solicitação; ocultar o botão na interface não substitui a autorização.
- Somente administradores podem remover participantes que não sejam administradores. A interface de remoção fica disponível apenas na página da turma, nunca na aba de membros de um calendário.
- A remoção dos vínculos com os calendários da turma é feita junto com a remoção do vínculo com a turma, para evitar que o participante continue acessando os calendários por associações remanescentes.
- Remover um participante não apaga calendários, eventos, a conta do usuário ou os vínculos dele com outras turmas.
- A confirmação deve ser enviada por uma requisição POST protegida contra CSRF; abrir a página ou cancelar a confirmação não pode alterar dados.
- A interface não deve oferecer a remoção do próprio ator nem de outro administrador. A saída voluntária é coberta pelo CDU-027.

## Implementação corrigida

A implementação garante que somente administradores da turma possam remover participantes comuns. A ação não é exibida para administradores como alvos nem na página de calendário; a view também valida a permissão e o tipo de vínculo para bloquear requisições diretas.

Na navegação, todos os participantes aparecem em uma lista única na aba **Membros**, sem distinção visual entre administradores e alunos, e sem aparecer junto à aba **Eventos**. A remoção aparece apenas para alunos na página da turma.

```python
# mysite/apps/turmas/views.py
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
```

```django
{# mysite/apps/core/templates/core/painel_membros.html #}
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
```

O botão e o modal aparecem somente para alunos na aba Membros da turma; administradores não podem ser removidos.

```css
/* mysite/apps/core/static/core/css/painel_membros.css */
.membro__acao {
    border: 1px solid transparent;
    border-radius: var(--raio);
    background: transparent;
    color: #8a2525;
    font: inherit;
    padding: 6px 10px;
    cursor: pointer;
}

.modal-remover-participante {
    width: min(420px, calc(100% - 32px));
    border: 0;
    border-radius: var(--raio-modal);
    box-shadow: var(--sombra-modal);
}
```

## Diagrama de Interação (Sequência)

[Código PlantUML do diagrama de sequência](diagramas_cdu_024.md#diagrama-de-sequência).

## Diagrama de Classes de Projeto

[Código PlantUML do diagrama de classes de projeto](diagramas_cdu_024.md#diagrama-de-classes-de-projeto).

## Guia de implementação

[Implementação detalhada do CDU-024](implementacao_cdu_024.md), incluindo arquivos alterados, migração de dados, interface, autorização e testes.
