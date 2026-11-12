(function () {
  const dialog = document.getElementById('modal-detalhes-evento');
  if (!dialog) return;

  const painelVer = dialog.querySelector('[data-painel="visualizar"]');
  const form = dialog.querySelector('[data-painel="editar"]');
  const btnEditar = dialog.querySelector('[data-acao="editar"]');
  const btnSalvar = form.querySelector('button[type="submit"]');

  let evento = null;
  let modo = 'visualizar';

  const campo = (nome) => form.querySelector(`[name="${nome}"]`);
  const texto = (nome, valor) => {
    dialog.querySelector(`[data-campo="${nome}"]`).textContent = valor;
  };


  function parseData(iso) {
    const [ano, mes, dia] = iso.split('-').map(Number);
    return new Date(ano, mes - 1, dia);
  }

  function formatarData(iso) {
    const texto = parseData(iso).toLocaleDateString('pt-BR', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
    });
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  function preencherVisualizacao(ev) {
    texto('calendario', ev.calendario);
    texto('titulo', ev.titulo);
    texto('data', formatarData(ev.data));
    texto('horario', `${ev.inicio} às ${ev.fim}`);
    texto('descricao', ev.descricao || 'Nenhuma descrição foi adicionada a este evento.');
    btnEditar.hidden = !ev.pode_editar;
  }

  function preencherFormulario(ev) {
    campo('titulo').value = ev.titulo;
    campo('data').value = ev.data;
    campo('inicio').value = ev.inicio;
    campo('fim').value = ev.fim;
    campo('descricao').value = ev.descricao;
  }

  function limparErros() {
    form.querySelectorAll('[data-erro]').forEach((el) => {
      el.hidden = true;
      el.textContent = '';
    });
  }

  function mostrarErros(erros) {
    Object.entries(erros).forEach(([nome, mensagens]) => {
      const el = form.querySelector(`[data-erro="${nome}"]`) ||
        form.querySelector('[data-erro="__all__"]');
      el.textContent = Array.isArray(mensagens) ? mensagens.join(' ') : mensagens;
      el.hidden = false;
    });
    const primeiro = form.querySelector('[data-erro]:not([hidden])');
    if (primeiro) primeiro.scrollIntoView({ block: 'nearest' });
  }

  function validar() {
    const erros = {};
    if (!campo('titulo').value.trim()) erros.titulo = 'Informe o título do evento.';
    if (!campo('data').value) erros.data = 'Informe a data.';
    if (!campo('inicio').value) erros.inicio = 'Informe o início.';
    if (!campo('fim').value) erros.fim = 'Informe o fim.';
    if (!erros.inicio && !erros.fim && campo('fim').value <= campo('inicio').value) {
      erros.fim = 'O fim deve ser depois do início.';
    }
    return erros;
  }

  function definirModo(novoModo) {
    modo = novoModo;
    painelVer.hidden = modo !== 'visualizar';
    form.hidden = modo !== 'editar';

    if (modo === 'editar') {
      limparErros();
      campo('titulo').focus();
    } else {
      btnEditar.focus();
    }
  }

  function cancelarEdicao() {
    preencherFormulario(evento);
    definirModo('visualizar');
  }

  async function abrir(id) {
    const modelo = dialog.dataset.urlDetalhes;
    try {
      const resp = await fetch(modelo.replace('/0/', `/${id}/`), {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      if (!resp.ok) throw new Error(resp.status);
      evento = await resp.json();
    } catch (e) {
      alert('Não foi possível carregar o evento. Tente novamente.');
      return;
    }

    preencherVisualizacao(evento);
    preencherFormulario(evento);
    painelVer.hidden = false;
    form.hidden = true;
    modo = 'visualizar';
    dialog.showModal();
  }

  // Abre ao clicar em qualquer elemento com data-evento-id (funciona
  // também para eventos criados dinamicamente pelo calendário).
  document.addEventListener('click', (e) => {
    const alvo = e.target.closest('[data-evento-id]');
    if (!alvo) return;
    e.preventDefault();
    abrir(alvo.dataset.eventoId);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const alvo = e.target.closest('[data-evento-id]');
    if (!alvo) return;
    e.preventDefault();
    abrir(alvo.dataset.eventoId);
  });

  dialog.addEventListener('click', (e) => {
    if (e.target.closest('[data-fechar]')) {
      dialog.close();
      return;
    }
    // lique no fundo escuro só fecha no modo visualização,
    // para não perder o que foi digitado.
    if (e.target === dialog && modo === 'visualizar') dialog.close();
  });

  btnEditar.addEventListener('click', () => definirModo('editar'));
  form.querySelector('[data-acao="cancelar"]').addEventListener('click', cancelarEdicao);

  // esc na edição cancela a edição em vez de fechar tudo.
  dialog.addEventListener('cancel', (e) => {
    if (modo === 'editar') {
      e.preventDefault();
      cancelarEdicao();
    }
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    limparErros();

    const erros = validar();
    if (Object.keys(erros).length) {
      mostrarErros(erros);
      return;
    }

    btnSalvar.disabled = true;
    try {
      const resp = await fetch(evento.url_atualizar, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const dados = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        mostrarErros(dados.erros || { __all__: 'Não foi possível salvar o evento.' });
        return;}
      window.location.reload();
    } catch (err) {
      mostrarErros({ __all__: 'Falha de conexão. Tente novamente.' });
    } finally {
      btnSalvar.disabled = false;
    }
  });
})();