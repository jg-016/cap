# CDU-010 — Códigos dos diagramas

Os diagramas abaixo representam o fluxo especificado no [CDU-010](cdu_010.md).
O formulário de edição é parte do projeto do caso de uso e ainda precisa ser
implementado.

## Diagrama de sequência

```plantuml
@startuml diagrama_interacoes_cdu_010
title CDU-010 - Atualizar calendário

skinparam maxMessageSize 220

actor Estudante
boundary "calendario.html" as TelaCalendario
control "calendarios.views.atualizar_calendario" as View
entity Calendario
entity MembroDeCalendario
boundary "Formulário de edição" as Formulario

Estudante -> TelaCalendario : seleciona "Editar calendário"
TelaCalendario -> View : GET /calendarios/atualizar_calendario/{id}
View -> Calendario : buscar calendário por id
Calendario --> View : calendário
View -> MembroDeCalendario : buscar vínculo do estudante com o calendário
MembroDeCalendario --> View : vínculo e papel de administrador

alt estudante é administrador
    View -> Formulario : renderizar nome e descrição atuais
    Formulario --> Estudante : exibir formulário
    alt estudante cancela antes do envio
        Estudante -> Formulario : selecionar "Cancelar"
        Formulario --> Estudante : retornar ao calendário sem salvar alterações
    else estudante envia alterações
        Estudante -> Formulario : alterar campos e enviar
        Formulario -> View : POST nome e descrição
        View -> Calendario : buscar calendário
        Calendario --> View : calendário
        View -> MembroDeCalendario : verificar permissão de administrador
        MembroDeCalendario --> View : resultado da verificação

        alt estudante é administrador
            alt dados válidos
                View -> Calendario : atualizar nome e descrição; salvar
                Calendario --> View : atualização concluída
                View --> Estudante : redirecionar para o calendário atualizado
            else dados inválidos
                View -> Formulario : renderizar erros mantendo os valores enviados
                Formulario --> Estudante : exibir campos para correção
            end
        else estudante não é administrador
            View --> Estudante : negar atualização e informar falta de permissão
        end
    end
else estudante não é administrador
    View --> Estudante : negar acesso e informar falta de permissão
end

@enduml
```

## Diagrama de classes de projeto

```plantuml
@startuml diagrama_classes_projeto_cdu_010
title CDU-010 - Classes de projeto

skinparam classAttributeIconSize 0
hide empty members

class "calendario.html" as TelaCalendario <<boundary>>
class "Formulário de edição\n(a implementar)" as Formulario <<boundary>>

class "calendarios.views" as Views <<control>> {
    +atualizar_calendario(request, id)
}

class Calendario <<entity>> {
    {field} +nome: CharField(100)
    {field} +descricao: CharField(500)
    +save()
}

class MembroDeCalendario <<entity>> {
    {field} +eh_admin: BooleanField
    {field} +usuario: ForeignKey(Usuario)
    {field} +calendario: ForeignKey(Calendario)
}

class Usuario <<entity>> {
    {field} +nome_completo: CharField(100)
    {field} +email: EmailField
}

TelaCalendario ..> Views : acessar edição
Views ..> Formulario : renderizar formulário e erros
Formulario ..> Views : enviar alterações
Views ..> Calendario : buscar e salvar alterações
Views ..> MembroDeCalendario : verificar permissão

Usuario "1" -- "0..*" MembroDeCalendario
Calendario "1" -- "0..*" MembroDeCalendario

@enduml
```
     