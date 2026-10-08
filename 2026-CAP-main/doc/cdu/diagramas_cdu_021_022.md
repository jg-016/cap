# Diagramas de classes de projeto — CDU 021 e CDU 022

Os diagramas PlantUML dos casos de uso foram separados dos documentos de fluxo para manter a documentação organizada. Eles preservam os elementos de controle e domínio e não incluem as classes de template/apresentação.

## CDU 021 — Adicionar calendário à turma

Fonte PlantUML: [cdu_021_class.puml](021/cdu_021_class.puml).

O diagrama mostra a view de associação, a validação de administrador e as relações de `Turma`, `Calendario`, `Usuario` e suas entidades de associação.

## CDU 022 — Remover calendário da turma

Fonte PlantUML: [cdu_022_class.puml](022/cdu_022_class.puml).

O diagrama mostra a view de remoção e a validação do vínculo com a turma. A remoção altera somente a associação opcional `Calendario.turma`; não apaga o calendário.
