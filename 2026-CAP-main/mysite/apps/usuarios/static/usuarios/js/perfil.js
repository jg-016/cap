document.addEventListener('DOMContentLoaded', function () {
    const botoes = document.getElementById('botoes');
    const botaoEditar = document.getElementById('botao-editar');
    const form = document.getElementById('form-perfil');
    const nomeTexto = document.getElementById('nome-texto');
    const nomeCampo = document.getElementById('nome-campo');
    const campoNome = document.getElementById('campo-nome');
    const emailTexto = document.getElementById('email-texto');
    const emailCampo = document.getElementById('email-campo');
    const campoEmail = document.getElementById('campo-email');
    const iniciais = document.getElementById('iniciais');
    const aviso = document.getElementById('aviso');
    const botaoExcluir = document.getElementById('botao-excluir');
    const modalExclusao = document.getElementById('modal-exclusao');
    const botaoCancelarExclusao = document.getElementById('botao-cancelar-exclusao');

    if (!botoes || !botaoEditar || !form) return;
    if (botaoExcluir && modalExclusao && botaoCancelarExclusao) {
    botaoExcluir.addEventListener('click', function () {
        modalExclusao.classList.add('visivel');
    });

    botaoCancelarExclusao.addEventListener('click', function () {
        modalExclusao.classList.remove('visivel');
    });
}

    botaoEditar.addEventListener('click', editar);

    function editar() {
        nomeTexto.style.display = 'none';
        nomeCampo.style.display = 'block';
        emailTexto.style.display = 'none';
        emailCampo.style.display = 'block';

        botoes.innerHTML = '';

        const botaoCancelar = document.createElement('button');
        botaoCancelar.type = 'button';
        botaoCancelar.className = 'botao';
        botaoCancelar.textContent = 'Cancelar';
        botaoCancelar.addEventListener('click', cancelarEdicao);

        const botaoSalvar = document.createElement('button');
        botaoSalvar.type = 'button';
        botaoSalvar.className = 'botao botao-escuro';
        botaoSalvar.textContent = 'Salvar';
        botaoSalvar.addEventListener('click', salvarEdicao);
        botoes.appendChild(botaoCancelar);
        botoes.appendChild(botaoSalvar);
    }

    function cancelarEdicao() {
        campoNome.value = nomeTexto.textContent.trim();
        campoEmail.value = emailTexto.textContent.trim();
        nomeCampo.style.display = 'none';
        nomeTexto.style.display = 'block';
        emailCampo.style.display = 'none';
        emailTexto.style.display = 'block';
        botoes.innerHTML = '';

        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'botao';
        botao.textContent = 'Editar perfil';
        botao.addEventListener('click', editar);
        botoes.appendChild(botao);
    }

    function salvarEdicao() {
        const nome = campoNome.value.trim();
        const email = campoEmail.value.trim();

        if (!nome || !email) {
            mostrarAviso('Nome e e-mail são obrigatórios.');
            return;
        }
        const dados = new FormData(form);

        fetch(form.action || window.location.href, {
            method: 'POST',
            body: dados,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(function (resposta) {
            if (!resposta.ok) {
                throw new Error();
            }
            return resposta.text();
        })
        .then(function () {
            nomeTexto.textContent = nome;
            emailTexto.textContent = email;
            atualizarIniciais(nome);
            cancelarEdicao();
            mostrarAviso('Perfil atualizado com sucesso.');
        })
        .catch(function () {
            mostrarAviso('Não foi possível atualizar o perfil.');
        });
    }

    function atualizarIniciais(nome) {
        const partes = nome.trim().split(' ').filter(Boolean);
        const letras = partes
            .slice(0, 2)
            .map(function (parte) {
                return parte[0].toUpperCase();
            })
            .join('');

        iniciais.textContent = letras || '?';
    }
    function mostrarAviso(mensagem) {
        aviso.textContent = mensagem;
        aviso.classList.add('visivel');
        setTimeout(function () {
            aviso.classList.remove('visivel');
        }, 3000);
    }
});