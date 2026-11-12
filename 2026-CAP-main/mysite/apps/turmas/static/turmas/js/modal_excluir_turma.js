document.addEventListener('click', (event) => {
    const botaoAbrir = event.target.closest('[data-abrir-modal="modal-excluir-turma"]');

    if (botaoAbrir) {
        document.getElementById('modal-excluir-turma')?.showModal();
        return;
    }
    const botaoFechar = event.target.closest('#modal-excluir-turma [data-fechar-modal]');

    if (botaoFechar) {
        botaoFechar.closest('dialog')?.close();
        return;
    }
    const modal = document.getElementById('modal-excluir-turma');

    if (event.target === modal) {
        const limites = modal.getBoundingClientRect();
        const clicouFora = event.clientX < limites.left
            || event.clientX > limites.right
            || event.clientY < limites.top
            || event.clientY > limites.bottom;

        if (clicouFora) {
            modal.close();
        }
    }
});
