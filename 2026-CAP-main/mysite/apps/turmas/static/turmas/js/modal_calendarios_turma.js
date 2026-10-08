document.querySelectorAll('.bloco-calendarios-turma [data-abrir-modal]').forEach((botao) => {
    botao.addEventListener('click', () => {
        const modal = document.getElementById(botao.dataset.abrirModal);
        modal?.showModal();
    });
});

document.querySelectorAll('.modal-calendarios-turma').forEach((modal) => {
    modal.querySelectorAll('[data-fechar-modal]').forEach((botao) => {
        botao.addEventListener('click', () => modal.close());
    });

    modal.addEventListener('click', (evento) => {
        if (evento.target === modal) {
            modal.close();
        }
    });
});
