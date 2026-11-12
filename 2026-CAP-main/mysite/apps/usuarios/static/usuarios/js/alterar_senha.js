document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('[data-form-senha]');
    if (!form) return;

    const atual = form.querySelector('[name="old_password"]');
    const nova = form.querySelector('[name="new_password1"]');
    const confirmacao = form.querySelector('[name="new_password2"]');
    const enviar = form.querySelector('[data-enviar]');
    const avisoConfirmacao = form.querySelector('[data-aviso-confirmacao]');
    const barras = form.querySelectorAll('.senha-forca span');

    const requisitos = {
        tamanho: (valor) => valor.length >= 8,
        numerico: (valor) => valor.length > 0 && !/^\d+$/.test(valor),
    };

    const itens = Object.keys(requisitos).map((nome) => ({
        elemento: form.querySelector('[data-requisito="' + nome + '"]'),
        valido: requisitos[nome],
    }));

    form.querySelectorAll('[data-alternar]').forEach(function (botao) {
        botao.addEventListener('click', function () {
            const campo = document.getElementById(botao.dataset.alternar);
            const mostrar = campo.type === 'password';

            campo.type = mostrar ? 'text' : 'password';
            botao.setAttribute('aria-pressed', String(mostrar));
            botao.setAttribute('aria-label', mostrar ? 'Ocultar senha' : 'Mostrar senha');
        });
    });

    function atualizar() {
        const valor = nova.value;
        let cumpridos = 0;

        itens.forEach(function (item) {
            const ok = item.valido(valor);
            item.elemento.classList.toggle('cumprido', ok);
            if (ok) cumpridos++;
        });

        barras.forEach(function (barra, indice) {
            barra.classList.toggle('ativa', indice < cumpridos);
        });

        const coincide = confirmacao.value.length > 0 && valor === confirmacao.value;
        avisoConfirmacao.hidden = !(confirmacao.value.length > 0 && !coincide);

        enviar.disabled = !(
            atual.value.length > 0 &&
            cumpridos === itens.length &&
            coincide
        );
    }

    [atual, nova, confirmacao].forEach(function (campo) {
        campo.addEventListener('input', atualizar);
    });

    atualizar();
});
