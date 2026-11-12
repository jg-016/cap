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

## Regras e observações

- A permissão deve ser conferida no servidor no momento da solicitação; ocultar o botão na interface não substitui a autorização.
- A remoção dos vínculos com os calendários da turma é feita junto com a remoção do vínculo com a turma, para evitar que o participante continue acessando os calendários por associações remanescentes.
- Remover um participante não apaga calendários, eventos, a conta do usuário ou os vínculos dele com outras turmas.
- A confirmação deve ser enviada por uma requisição POST protegida contra CSRF; abrir a página ou cancelar a confirmação não pode alterar dados.
- A interface não deve oferecer a remoção do próprio ator. A saída voluntária é coberta pelo CDU-027.

> **Nota de implementação:** este documento especifica o comportamento esperado. A rota e a ação de remoção de participante ainda precisam ser implementadas no aplicativo.

## Diagrama de Interação (Sequência)

[Código PlantUML do diagrama de sequência](diagramas_cdu_024.md#diagrama-de-sequência).

## Diagrama de Classes de Projeto

[Código PlantUML do diagrama de classes de projeto](diagramas_cdu_024.md#diagrama-de-classes-de-projeto).
