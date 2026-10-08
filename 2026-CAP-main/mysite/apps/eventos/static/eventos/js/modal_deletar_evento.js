const modalDeletarEvento = document.getElementById('modal-deletar-evento');

document.querySelectorAll('[data-abrir-modal="modal-deletar-evento"]').forEach(botao => {
    botao.addEventListener('click', () => modalDeletarEvento.showModal());
});

modalDeletarEvento?.querySelectorAll('[data-fechar-modal]').forEach(botao => {
    botao.addEventListener('click', () => modalDeletarEvento.close());
});
