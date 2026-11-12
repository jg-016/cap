// Esse arquivo serve para os submenus nas telas de calendário e turma.

const submenu = document.querySelector('main .submenu');
const itensMenu = submenu.querySelectorAll('li')

if (submenu.querySelectorAll('li.ativo').length === 0) {
    itensMenu[0].classList.add('ativo')
}

function encontrarPainel(itemMenu) {
    const idPainel = itemMenu.dataset.idPainel
    const painel = document.getElementById(idPainel)
    return painel
}

function exibirSomentePaineisAtivos() {
    const itensMenuInativos = submenu.querySelectorAll('li:not(.ativo)')

    itensMenuInativos.forEach((itemMenu) => {
        const painel = encontrarPainel(itemMenu)
        painel?.classList.add('oculto')
    })

    let itemMenuAtivo = submenu.querySelector('li.ativo')

    const painelAtivo = encontrarPainel(itemMenuAtivo)
    painelAtivo?.classList.remove('oculto')
}

function atualizarAriaSelected() {
    itensMenu.forEach((itemMenu) => {
        itemMenu.setAttribute('aria-selected', itemMenu.classList.contains('ativo'))
    })
}

function ativarItemMenu(itemMenu) {
    const itemMenuAtivo = submenu.querySelector('li.ativo')
    itemMenuAtivo.classList.remove('ativo')
    itemMenu.classList.add('ativo')
    atualizarAriaSelected()
}

itensMenu.forEach((itemMenu) => {
    itemMenu.addEventListener('click', () => {
        ativarItemMenu(itemMenu)
        exibirSomentePaineisAtivos()
    })
    itemMenu.addEventListener('keydown', (evento) => {
        if (evento.key === 'Enter' || evento.key === ' ') {
            evento.preventDefault()
            ativarItemMenu(itemMenu)
            exibirSomentePaineisAtivos()
        }
    })
})

atualizarAriaSelected()
exibirSomentePaineisAtivos()