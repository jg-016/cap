# Alteracoes na pagina de detalhes do evento

Este documento registra as mudancas recentes na pagina de detalhes do evento. Ele complementa a documentacao existente sem substitui-la.

## Pagina do evento

- O layout foi aprimorado com melhor hierarquia visual, linhas de informacao organizadas e ajustes para telas menores.
- O botao **Deletar evento** recebeu estilos proprios, incluindo estados de hover, clique e foco acessivel.
- O botao e o modal de exclusao do calendario foram removidos desta pagina.
- O link de retorno leva ao calendario geral.
- A exclusao do evento e enviada por formulario POST e retorna ao calendario geral.
- O link do CSS usa uma versao na URL para evitar que o navegador mantenha estilos antigos em cache.

## Desenvolvimento local

- A configuracao de desenvolvimento passou a confiar nas origens `http://localhost:8001` e `https://localhost:8001` para evitar falhas CSRF ao testar nessa porta. Essa alteracao nao modifica as configuracoes de producao.

## Validacao

Os testes da aplicacao de eventos foram executados com:

```bash
python manage.py test apps.eventos.tests
```

Resultado: 4 testes aprovados.

## Codigo da pagina

Os blocos abaixo reproduzem a implementacao atual. Os arquivos executaveis continuam nas pastas indicadas nos titulos.

### Template: `apps/eventos/templates/eventos/visualizar_evento.html`

```django
{% extends 'core/base.html' %}

{% block title %}{{ evento.nome }}{% endblock %}

{% block extra_css %}
	{% load static %}
	<link rel="stylesheet" href="{% static 'eventos/css/visualizar_evento.css' %}?v=2">
{% endblock %}

{% block content %}
<section class="evento-detalhes" aria-labelledby="evento-titulo">
	<a class="evento-detalhes__voltar" href="{% url 'inicio' %}">
		<span class="material-symbols-outlined" aria-hidden="true">arrow_back</span>
		Voltar ao calendário geral
	</a>

	<header class="evento-detalhes__cabecalho">
		<p class="evento-detalhes__sobretitulo">Detalhes do evento</p>
		<h1 id="evento-titulo">{{ evento.nome }}</h1>
	</header>

	<dl>
		<div class="evento-detalhes__linha evento-detalhes__linha--descricao">
			<dt>Descrição</dt>
			<dd>{{ evento.conteudo|default:"Sem descrição." }}</dd>
		</div>
		<div class="evento-detalhes__linha">
			<dt>Data</dt>
			<dd>{{ evento.inicio|date:"d/m/Y" }}</dd>
		</div>
		<div class="evento-detalhes__linha">
			<dt>Horário</dt>
			<dd>{{ evento.inicio|date:"H:i" }} - {{ evento.fim|date:"H:i" }}</dd>
		</div>
		<div class="evento-detalhes__linha">
			<dt>Calendário</dt>
			<dd>{{ evento.calendario.nome }}</dd>
		</div>
	</dl>

	{% if usuario_eh_admin %}
		<div class="evento-detalhes__acoes">
			<form method="post" action="{% url 'eventos:deletar_evento' evento.id %}">
				{% csrf_token %}
				<button class="evento-detalhes__deletar-evento" type="submit">Deletar evento</button>
			</form>
		</div>
	{% endif %}
</section>
{% endblock %}
```

### Views: `apps/eventos/views.py`

```python
@login_required
def visualizar_evento(request, id):
	evento = get_object_or_404(
		Evento.objects.select_related('calendario'),
		id=id,
		calendario__usuarios=request.user,
	)
	membro = get_object_or_404(
		MembroDeCalendario,
		calendario=evento.calendario,
		usuario=request.user,
	)

	return render(
		request,
		'eventos/visualizar_evento.html',
		{'evento': evento, 'usuario_eh_admin': membro.eh_admin},
	)


@login_required
def deletar_evento(request, id):
	evento = get_object_or_404(
		Evento.objects.select_related('calendario'),
		id=id,
		calendario__usuarios=request.user,
	)
	membro = get_object_or_404(
		MembroDeCalendario,
		calendario=evento.calendario,
		usuario=request.user,
	)

	if not membro.eh_admin:
		return redirect('eventos:visualizar_evento', id=evento.id)

	if request.method == 'POST':
		evento.delete()
		return redirect('inicio')

	return redirect('eventos:visualizar_evento', id=evento.id)
```

### CSS: `apps/eventos/static/eventos/css/visualizar_evento.css`

```css
.evento-detalhes {
	width: 100%;
	max-width: 760px;
	margin: auto;
	padding: clamp(24px, 5vw, 48px);
	background: linear-gradient(145deg, #ffffff 0%, #f7fafb 100%);
	border: 1px solid #dce5e8;
	border-radius: 8px;
	box-shadow: 0 16px 42px rgba(28, 52, 61, 0.09);
}

.evento-detalhes__voltar {
	display: inline-block;
	margin-bottom: 36px;
	color: #176b72;
	font-size: 14px;
	font-weight: 600;
	text-decoration: none;
}

.evento-detalhes__voltar .material-symbols-outlined {
	margin-right: 6px;
	vertical-align: -5px;
	font-size: 19px;
}

.evento-detalhes__voltar:hover {
	text-decoration: underline;
}

.evento-detalhes__cabecalho {
	margin-bottom: 20px;
	padding-bottom: 24px;
	border-bottom: 2px solid #e7edef;
}

.evento-detalhes__sobretitulo {
	margin: 0 0 8px;
	color: #176b72;
	font-size: 12px;
	font-weight: 700;
	text-transform: uppercase;
}

.evento-detalhes h1 {
	margin: 0;
	color: #172a32;
	font-size: 36px;
	line-height: 1.15;
	overflow-wrap: anywhere;
}

.evento-detalhes dl {
	display: flex;
	flex-direction: column;
	gap: 0;
	margin: 0;
}

.evento-detalhes__linha {
	display: grid;
	grid-template-columns: minmax(120px, 0.32fr) minmax(0, 1fr);
	gap: 24px;
	padding: 16px 12px;
	border-bottom: 1px solid #e7edef;
	border-radius: 4px;
}

.evento-detalhes__linha:nth-child(odd) {
	background: rgba(229, 238, 239, 0.38);
}

.evento-detalhes__linha dt {
	color: #607078;
	font-size: 14px;
	font-weight: 600;
}

.evento-detalhes__linha dd {
	color: #1c3038;
	margin: 0;
	line-height: 1.55;
	overflow-wrap: anywhere;
}

.evento-detalhes__acoes {
	display: flex;
	flex-wrap: wrap;
	gap: 12px;
	margin-top: 26px;
	padding-top: 22px;
	border-top: 1px solid #dce5e8;
}

.evento-detalhes__acoes form {
	margin: 0;
}

.evento-detalhes .evento-detalhes__deletar-evento {
	display: inline-flex;
	min-height: 44px;
	align-items: center;
	justify-content: center;
	padding: 10px 18px;
	border: 1px solid #a9211e;
	border-radius: 6px;
	appearance: none;
	background: #bd302b;
	color: #ffffff;
	font-family: inherit;
	font-size: 14px;
	font-weight: 700;
	cursor: pointer;
	box-shadow: 0 2px 4px rgba(102, 27, 24, 0.16);
	transition: background-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
}

.evento-detalhes .evento-detalhes__deletar-evento:hover {
	border-color: #851d1a;
	background: #98251f;
	box-shadow: 0 4px 10px rgba(102, 27, 24, 0.22);
	transform: translateY(-1px);
}

.evento-detalhes .evento-detalhes__deletar-evento:active {
	box-shadow: none;
	transform: translateY(0);
}

.evento-detalhes .evento-detalhes__deletar-evento:focus-visible {
	outline: 3px solid rgba(189, 48, 43, 0.28);
	outline-offset: 3px;
}

@media (max-width: 600px) {
	.evento-detalhes {
		margin: 24px 0;
		padding: 24px 20px;
	}

	.evento-detalhes__voltar {
		margin-bottom: 28px;
	}

	.evento-detalhes h1 {
		font-size: 30px;
	}

	.evento-detalhes__linha {
		grid-template-columns: 1fr;
		gap: 6px;
		padding: 14px 10px;
	}

	.evento-detalhes__acoes,
	.evento-detalhes__acoes form,
	.evento-detalhes .evento-detalhes__deletar-evento {
		width: 100%;
	}
}
```