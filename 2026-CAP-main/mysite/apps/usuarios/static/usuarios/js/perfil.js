
document.addEventListener('DOMContentLoaded', function () {
    const botoes = document.getElementById('botoes');
    const botaoEditar = document.getElementById('botao-editar');
    const form = document.getElementById('form-perfil');

    const nomeTexto = document.getElementById('nome-texto');
    const nomeCampo = document.getElementById('nome-campo');
    const campoNome = document.getElementById('campo-nome');
    const iniciais = document.getElementById('iniciais');

    const acoesEdicao = document.getElementById('acoes-edicao');

    const botaoExcluir = document.getElementById('botao-excluir');
    const modalExclusao = document.getElementById('modal-exclusao');
    const botaoCancelarExclusao = document.getElementById('botao-cancelar-exclusao');

    if (!botoes || !botaoEditar || !form) return;

    // abrir modal de exclusão
    if (botaoExcluir && modalExclusao && botaoCancelarExclusao) {
        botaoExcluir.addEventListener('click', function () {
            modalExclusao.classList.add('visivel');
        });

        botaoCancelarExclusao.addEventListener('click', function () {
            modalExclusao.classList.remove('visivel');
        });
    }

    // entrar no modo de edição
    botaoEditar.addEventListener('click', editar);

    function editar() {
        nomeTexto.style.display = 'none';
        nomeCampo.style.display = 'block';

        acoesEdicao.classList.add('visivel');
        botoes.innerHTML = '';

        const botaoCancelar = document.createElement('button');
        botaoCancelar.type = 'button';
        botaoCancelar.className = 'botao';
        botaoCancelar.textContent = 'Cancelar';
        botaoCancelar.addEventListener('click', cancelarEdicao);

        const botaoSalvar = document.createElement('button');
        botaoSalvar.type = 'submit';
        botaoSalvar.className = 'botao botao-escuro';
        botaoSalvar.textContent = 'Salvar';

        botoes.appendChild(botaoCancelar);
        botoes.appendChild(botaoSalvar);
    }

    // Cancelar edição
    function cancelarEdicao() {
        campoNome.value = nomeTexto.textContent.trim();
        nomeCampo.style.display = 'none';
        nomeTexto.style.display = 'block';

        acoesEdicao.classList.remove('visivel');

        botoes.innerHTML = '';
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'botao';
        botao.textContent = 'Editar perfil';
        botao.addEventListener('click', editar);

        botoes.appendChild(botao);
    }
});
