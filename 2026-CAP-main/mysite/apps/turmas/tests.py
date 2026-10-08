from django.test import TestCase
from django.urls import reverse

from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.turmas.models import MembroDeTurma, Turma
from apps.usuarios.models import Usuario


class AtualizarTurmaTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email='admin-turma@teste.com',
            password='Senha@123',
            nome_completo='Admin Turma',
        )
        self.membro = Usuario.objects.create_user(
            email='membro-turma@teste.com',
            password='Senha@123',
            nome_completo='Membro Turma',
        )
        self.turma = Turma.objects.create(
            nome='Turma original',
            descricao='Descrição original',
        )
        MembroDeTurma.objects.create(
            usuario=self.admin,
            turma=self.turma,
            eh_admin=True,
            numero_paleta=1,
        )
        MembroDeTurma.objects.create(
            usuario=self.membro,
            turma=self.turma,
            eh_admin=False,
            numero_paleta=2,
        )

    def test_atualizar_turma_altera_nome_e_descricao(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('atualizar_turma', args=[self.turma.id]),
            {'nome': 'Turma atualizada', 'descricao': 'Nova descrição'},
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.turma.refresh_from_db()
        self.assertEqual(self.turma.nome, 'Turma atualizada')
        self.assertEqual(self.turma.descricao, 'Nova descrição')

    def test_membro_comum_nao_pode_atualizar_turma(self):
        self.client.force_login(self.membro)

        response = self.client.post(
            reverse('atualizar_turma', args=[self.turma.id]),
            {'nome': 'Alteração não permitida', 'descricao': 'Descrição'},
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.turma.refresh_from_db()
        self.assertEqual(self.turma.nome, 'Turma original')
        self.assertEqual(self.turma.descricao, 'Descrição original')

    def test_get_atualizar_turma_redireciona_para_detalhes(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('atualizar_turma', args=[self.turma.id])
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))

    def test_pagina_da_turma_exibe_modal_para_administrador(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('turma', args=[self.turma.id]))

        self.assertContains(response, '<dialog')
        self.assertContains(response, 'data-abrir-modal="modal-atualizar-turma"')
        self.assertContains(
            response,
            reverse('atualizar_turma', args=[self.turma.id]),
        )

    def test_nome_vazio_nao_atualiza_turma_e_exibe_erro(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('atualizar_turma', args=[self.turma.id]),
            {'nome': ' ', 'descricao': 'Descrição alterada'},
            follow=True,
        )

        self.turma.refresh_from_db()
        self.assertEqual(self.turma.nome, 'Turma original')
        self.assertEqual(self.turma.descricao, 'Descrição original')
        self.assertContains(response, 'nome')

    def test_admin_pode_adicionar_calendario_a_turma(self):
        self.client.force_login(self.admin)
        calendario = Calendario.objects.create(
            nome='Calendário pessoal',
            descricao='Disponível para associação',
            turma=None,
        )
        MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario,
            eh_admin=True,
            numero_paleta=3,
        )

        response = self.client.post(
            reverse('adicionar_calendario_turma', args=[self.turma.id, calendario.id]),
            follow=True,
        )

        calendario.refresh_from_db()
        self.assertEqual(calendario.turma, self.turma)
        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))

    def test_admin_pode_remover_calendario_da_turma(self):
        self.client.force_login(self.admin)
        calendario = Calendario.objects.create(
            nome='Calendário da turma',
            descricao='Para remover',
            turma=self.turma,
        )
        MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario,
            eh_admin=True,
            numero_paleta=4,
        )

        response = self.client.post(
            reverse('remover_calendario_turma', args=[self.turma.id, calendario.id]),
            follow=True,
        )

        calendario.refresh_from_db()
        self.assertIsNone(calendario.turma)
        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
