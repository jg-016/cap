const modalAtualizarTurma = document.getElementById('modal-atualizar-turma');

document.querySelectorAll('[data-abrir-modal="modal-atualizar-turma"]').forEach(botao => {
    botao.addEventListener('click', () => modalAtualizarTurma.showModal());
});

modalAtualizarTurma?.querySelectorAll('[data-fechar-modal]').forEach(botao => {
    botao.addEventListener('click', () => modalAtualizarTurma.close());
});
