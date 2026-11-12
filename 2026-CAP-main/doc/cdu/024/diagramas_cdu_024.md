# CDU-024 — Códigos dos diagramas

Os diagramas abaixo descrevem a proposta de interação e de classes de projeto
para o [CDU-024](cdu_024_completo.md). Os códigos podem ser copiados para um
renderizador PlantUML.

## Diagrama de sequência

```plantuml
@startuml diagrama_interacoes_cdu_024
title CDU-024 - Remover participante de turma

skinparam maxMessageSize 220

actor "Estudante administrador" as Admin
boundary "turma.html\npainel_membros.html" as Tela
control "turmas.views.remover_participante_turma" as View
entity Turma
entity MembroDeTurma
entity Calendario
entity MembroDeCalendario

Admin -> Tela : acessa a aba "Membros"
Tela -> View : GET /turmas/<turma_id>
View -> Turma : buscar turma
Turma --> View : turma
View -> MembroDeTurma : verificar vínculo administrador
MembroDeTurma --> View : ator autorizado
View -> MembroDeTurma : listar participantes da turma
MembroDeTurma --> View : participantes
View --> Tela : renderizar participantes e ações

Admin -> Tela : seleciona "Remover" para outro participante
Tela --> Admin : exibe confirmação com o nome do participante
Admin -> Tela : confirma a remoção
Tela -> View : POST /turmas/<turma_id>/participantes/<usuario_id>/remover
View -> Turma : buscar turma
Turma --> View : turma
View -> MembroDeTurma : verificar novamente permissão do ator
MembroDeTurma --> View : resultado da autorização
View -> MembroDeTurma : buscar vínculo do participante com a turma
MembroDeTurma --> View : vínculo do participante ou ausência

alt ator não é administrador
    View --> Admin : negar operação; vínculos permanecem inalterados
else turma ou participação do alvo não existe
    View --> Admin : responder recurso não encontrado; não alterar dados
else alvo é o próprio ator
    View --> Admin : negar remoção própria; orientar uso do CDU-027
else ator autorizado e alvo pertence à turma
    group operação atômica
        View -> MembroDeTurma : remover vínculo do alvo com a turma
        View -> Calendario : localizar calendários associados à turma
        Calendario --> View : calendários da turma
        View -> MembroDeCalendario : remover vínculos do alvo com esses calendários
    end
    View --> Admin : redirecionar à turma com confirmação de sucesso
    View -> MembroDeTurma : listar participantes atualizados
    MembroDeTurma --> View : lista sem o participante removido
    View --> Tela : renderizar lista atualizada
end

@enduml
```

## Diagrama de classes de projeto

```plantuml
@startuml diagrama_classes_projeto_cdu_024
title CDU-024 - Classes de projeto

skinparam classAttributeIconSize 0
hide empty members

class "turma.html\npainel_membros.html\nconfirmação de remoção" as Tela <<boundary>>

class "turmas.views" as Views <<control>> {
    +turma(request, id)
    +remover_participante_turma(request, turma_id, usuario_id)
}

class Turma <<entity>> {
    {field} +id
    {field} +nome: CharField(100)
}

class MembroDeTurma <<entity>> {
    {field} +eh_admin: BooleanField
    {field} +usuario: ForeignKey(Usuario)
    {field} +turma: ForeignKey(Turma)
    +delete()
}

class Calendario <<entity>> {
    {field} +turma: ForeignKey(Turma)
}

class MembroDeCalendario <<entity>> {
    {field} +usuario: ForeignKey(Usuario)
    {field} +calendario: ForeignKey(Calendario)
    +delete()
}

class Usuario <<entity>> {
    {field} +nome_completo: CharField(100)
    {field} +email: EmailField
}

Tela ..> Views : exibir lista e enviar POST
Views ..> Turma : buscar turma
Views ..> MembroDeTurma : autorizar e remover participação
Views ..> Calendario : obter calendários associados
Views ..> MembroDeCalendario : revogar acesso aos calendários da turma

Turma "1" -- "0..*" MembroDeTurma
Usuario "1" -- "0..*" MembroDeTurma
Turma "1" -- "0..*" Calendario
Calendario "1" -- "0..*" MembroDeCalendario
Usuario "1" -- "0..*" MembroDeCalendario

note bottom of Views
  A remoção do vínculo com a turma
  e dos vínculos com seus calendários
  deve ocorrer em uma única transação.
end note


@enduml
```
