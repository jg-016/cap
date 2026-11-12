from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse

from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.eventos.models import Evento
from apps.usuarios.models import Usuario


class CalendarioViewTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='teste@teste.com',
            password='Senha@123',
            nome_completo='Usuário Teste',
        )
        self.calendario = Calendario.objects.create(
            nome='Calendário Teste',
            descricao='Descrição do calendário',
        )
        MembroDeCalendario.objects.create(
            usuario=self.usuario,
            calendario=self.calendario,
            eh_admin=True,
            numero_paleta=1,
        )

    def test_calendario_exibe_visualizacao_semanal(self):
        evento = Evento.objects.create(
            nome='Reunião do grupo',
            conteudo='Planejamento da semana',
            inicio=datetime(2026, 8, 12, 9, 0, 0),
            fim=datetime(2026, 8, 12, 10, 30, 0),
            calendario=self.calendario,
        )

        self.client.force_login(self.usuario)
        sessao = self.client.session
        sessao['dia_em_foco'] = '2026-08-12'
        sessao.save()
        response = self.client.get(reverse('calendario', args=[self.calendario.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'painel-eventos')
        self.assertContains(response, evento.nome)

    def test_criar_evento_redireciona_para_o_calendario(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse('eventos:criar_evento'),
            {
                'titulo': 'Nova tarefa',
                'calendario': self.calendario.id,
                'data': '2026-08-12',
                'inicio': '09:00',
                'fim': '10:00',
                'descricao': 'Descrição da tarefa',
            },
        )

        self.assertRedirects(response, reverse('calendario', args=[self.calendario.id]))
        self.assertTrue(
            Evento.objects.filter(
                calendario=self.calendario,
                nome='Nova tarefa',
            ).exists()
        )


class AtualizarCalendarioTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email='admin-calendario@teste.com',
            password='Senha@123',
            nome_completo='Admin Calendário',
        )
        self.membro = Usuario.objects.create_user(
            email='membro-calendario@teste.com',
            password='Senha@123',
            nome_completo='Membro Calendário',
        )
        self.visitante = Usuario.objects.create_user(
            email='visitante-calendario@teste.com',
            password='Senha@123',
            nome_completo='Visitante',
        )
        self.calendario = Calendario.objects.create(
            nome='Calendário original',
            descricao='Descrição original',
        )
        MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=self.calendario,
            eh_admin=True,
            numero_paleta=1,
        )
        MembroDeCalendario.objects.create(
            usuario=self.membro,
            calendario=self.calendario,
            eh_admin=False,
            numero_paleta=2,
        )
        self.url = reverse('atualizar_calendario', args=[self.calendario.id])

    def test_get_exibe_formulario_com_dados_atuais_e_cancelamento(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calendário original')
        self.assertContains(response, 'Descrição original')
        self.assertContains(response, 'formulario-calendario paleta-1')
        self.assertContains(response, 'Cancelar')
        self.assertContains(
            response,
            f'href="{reverse("calendario", args=[self.calendario.id])}"',
        )
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_post_valido_atualiza_e_redireciona_com_confirmacao(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {'nome': 'Calendário atualizado', 'descricao': 'Nova descrição'},
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse('calendario', args=[self.calendario.id]),
        )
        self.calendario.refresh_from_db()
        self.assertEqual(self.calendario.nome, 'Calendário atualizado')
        self.assertEqual(self.calendario.descricao, 'Nova descrição')
        self.assertContains(response, 'Calendário atualizado com sucesso.')
        self.assertContains(response, 'calendario-mensagem--success')
        self.assertContains(
            response,
            'calendarios/css/atualizar_calendario.css',
        )

    def test_post_invalido_preserva_valores_e_nao_atualiza_modelo(self):
        nome_invalido = 'N' * 101
        descricao_invalida = 'D' * 501
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {'nome': nome_invalido, 'descricao': descricao_invalida},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, nome_invalido)
        self.assertContains(response, descricao_invalida)
        self.assertTrue(response.context['form'].errors)
        self.calendario.refresh_from_db()
        self.assertEqual(self.calendario.nome, 'Calendário original')
        self.assertEqual(self.calendario.descricao, 'Descrição original')

    def test_nome_obrigatorio_nao_pode_ser_enviado_vazio(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {'nome': '  ', 'descricao': 'Descrição enviada'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['nome'])
        self.calendario.refresh_from_db()
        self.assertEqual(self.calendario.nome, 'Calendário original')

    def test_post_sem_dados_e_rejeitado_com_erros(self):
        self.client.force_login(self.admin)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 200)
        self.assertIn('nome', response.context['form'].errors)
        self.calendario.refresh_from_db()
        self.assertEqual(self.calendario.nome, 'Calendário original')

    def test_nao_admin_e_usuario_sem_vinculo_recebem_403_sem_alteracao(self):
        self.client.force_login(self.membro)
        resposta_membro = self.client.post(
            self.url,
            {'nome': 'Alteração indevida', 'descricao': 'Não salvar'},
        )

        self.client.force_login(self.visitante)
        resposta_visitante = self.client.get(self.url)

        self.assertEqual(resposta_membro.status_code, 403)
        self.assertContains(
            resposta_membro,
            'Somente administradores podem atualizar este calendário.',
            status_code=403,
        )
        self.assertEqual(resposta_visitante.status_code, 403)
        self.calendario.refresh_from_db()
        self.assertEqual(self.calendario.nome, 'Calendário original')
        self.assertEqual(self.calendario.descricao, 'Descrição original')
