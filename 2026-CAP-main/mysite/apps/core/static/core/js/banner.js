// Botões de copiar do banner (ex.: código da turma).

function copiarComSelecao(texto) {
    // Alternativa para navegadores que bloqueiam navigator.clipboard.
    const campo = document.createElement('textarea')
    campo.value = texto
    campo.setAttribute('readonly', '')
    campo.style.position = 'fixed'
    campo.style.opacity = '0'
    document.body.appendChild(campo)
    campo.select()

    let copiou = false
    try {
        copiou = document.execCommand('copy')
    } catch {
        copiou = false
    }

    campo.remove()
    return copiou
}

async function copiar(texto) {
    try {
        await navigator.clipboard.writeText(texto)
        return true
    } catch {
        return copiarComSelecao(texto)
    }
}

document.querySelectorAll('.banner [data-copiar]').forEach((botao) => {
    const conteudoOriginal = botao.innerHTML

    botao.addEventListener('click', async () => {
        if (!await copiar(botao.dataset.copiar)) {
            return
        }

        botao.classList.add('copiado')
        botao.textContent = 'Copiado'

        setTimeout(() => {
            botao.classList.remove('copiado')
            botao.innerHTML = conteudoOriginal
        }, 1500)
    })
})
