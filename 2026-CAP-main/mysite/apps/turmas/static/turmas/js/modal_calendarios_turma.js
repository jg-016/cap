document.addEventListener('click', (event) => {
    const openButton = event.target.closest('.calendarios-turma [data-abrir-modal]');
    if (openButton) {
        document.getElementById(openButton.dataset.abrirModal)?.showModal();
        return;
    }

    const closeButton = event.target.closest('.calendarios-turma [data-fechar-modal]');
    if (closeButton) {
        closeButton.closest('dialog')?.close();
        return;
    }

    if (event.target instanceof HTMLDialogElement && event.target.open) {
        const bounds = event.target.getBoundingClientRect();
        const clickedBackdrop = event.clientX < bounds.left
            || event.clientX > bounds.right
            || event.clientY < bounds.top
            || event.clientY > bounds.bottom;
        if (clickedBackdrop) {
            event.target.close();
        }
    }
});