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
        self.admin_membro_turma = MembroDeTurma.objects.create(
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

    def test_atualizar_turma_sincroniza_apenas_paleta_do_usuario(self):
        calendario_turma = Calendario.objects.create(
            nome='Calendário da turma',
            turma=self.turma,
        )
        membro_calendario_admin = MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario_turma,
            eh_admin=True,
            numero_paleta=1,
        )
        membro_calendario = MembroDeCalendario.objects.create(
            usuario=self.membro,
            calendario=calendario_turma,
            eh_admin=False,
            numero_paleta=2,
        )
        calendario_pessoal = Calendario.objects.create(nome='Calendário pessoal')
        membro_calendario_pessoal = MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario_pessoal,
            eh_admin=True,
            numero_paleta=3,
        )
        self.client.force_login(self.admin)

        self.client.post(
            reverse('atualizar_turma', args=[self.turma.id]),
            {
                'nome': 'Turma atualizada',
                'descricao': 'Nova descrição',
                'numero_paleta': '4',
            },
        )

        self.admin_membro_turma.refresh_from_db()
        membro_calendario_admin.refresh_from_db()
        membro_calendario.refresh_from_db()
        membro_calendario_pessoal.refresh_from_db()
        self.assertEqual(self.admin_membro_turma.numero_paleta, 4)
        self.assertEqual(membro_calendario_admin.numero_paleta, 4)
        self.assertTrue(membro_calendario_admin.eh_admin)
        self.assertEqual(membro_calendario.numero_paleta, 2)
        self.assertEqual(membro_calendario_pessoal.numero_paleta, 3)

    def test_paleta_invalida_impede_atualizar_turma(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('atualizar_turma', args=[self.turma.id]),
            {
                'nome': 'Nome não deve ser salvo',
                'descricao': 'Descrição não deve ser salva',
                'numero_paleta': '8',
            },
            follow=True,
        )

        self.turma.refresh_from_db()
        self.admin_membro_turma.refresh_from_db()
        self.assertEqual(self.turma.nome, 'Turma original')
        self.assertEqual(self.turma.descricao, 'Descrição original')
        self.assertEqual(self.admin_membro_turma.numero_paleta, 1)
        self.assertContains(response, 'Selecione uma cor válida para a turma.')

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
        self.assertContains(response, 'Calendários da turma')
        self.assertContains(response, 'modal-criar-calendario-turma')
        self.assertContains(response, 'Criar calendário de turma')
        self.assertContains(response, 'Cor da turma')
        self.assertContains(response, 'name="numero_paleta"')
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

    def test_associar_calendario_existente_sincroniza_paletas_e_preserva_permissoes(self):
        calendario = Calendario.objects.create(nome='Calendário pessoal')
        membro_admin = MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario,
            eh_admin=True,
            numero_paleta=6,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('adicionar_calendario', args=[self.turma.id]),
            {'calendario_id': calendario.id},
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        calendario.refresh_from_db()
        membro_admin.refresh_from_db()
        membro_calendario = MembroDeCalendario.objects.get(
            usuario=self.membro,
            calendario=calendario,
        )
        self.assertEqual(calendario.turma_id, self.turma.id)
        self.assertEqual(membro_admin.numero_paleta, 1)
        self.assertTrue(membro_admin.eh_admin)
        self.assertEqual(membro_calendario.numero_paleta, 2)
        self.assertFalse(membro_calendario.eh_admin)

    def test_criar_calendario_para_turma_cria_vinculos_dos_membros(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('criar_calendario_turma', args=[self.turma.id]),
            {'nome': 'Agenda da turma', 'descricao': 'Atividades'},
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        calendario = Calendario.objects.get(nome='Agenda da turma')
        self.assertEqual(calendario.turma_id, self.turma.id)
        self.assertEqual(
            MembroDeCalendario.objects.filter(calendario=calendario).count(),
            2,
        )
        self.assertEqual(
            MembroDeCalendario.objects.get(usuario=self.admin, calendario=calendario).numero_paleta,
            1,
        )
        self.assertEqual(
            MembroDeCalendario.objects.get(usuario=self.membro, calendario=calendario).numero_paleta,
            2,
        )

    # Teste de autorização da funcionalidade antiga, preservado para
    # desenvolvedores:
    # def test_membro_comum_nao_pode_associar_calendario(self):
    #     calendario = Calendario.objects.create(nome='Calendário pessoal')
    #     MembroDeCalendario.objects.create(
    #         usuario=self.admin,
    #         calendario=calendario,
    #         eh_admin=True,
    #         numero_paleta=1,
    #     )
    #     self.client.force_login(self.membro)
    #
    #     response = self.client.post(
    #         reverse('adicionar_calendario', args=[self.turma.id]),
    #         {'calendario_id': calendario.id},
    #     )
    #
    #     self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
    #     calendario.refresh_from_db()
    #     self.assertIsNone(calendario.turma_id)

    def test_remover_calendario_desvincula_sem_exclui_lo(self):
        calendario = Calendario.objects.create(
            nome='Calendário da turma',
            turma=self.turma,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'remover_calendario_turma',
                args=[self.turma.id, calendario.id],
            )
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertFalse(Calendario.objects.filter(id=calendario.id).exists())

    def test_rota_generica_remove_calendario_informado_no_post(self):
        calendario = Calendario.objects.create(
            nome='Calendário da turma',
            turma=self.turma,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('remover_calendario', args=[self.turma.id]),
            {'calendario_id': calendario.id},
        )
        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertFalse(Calendario.objects.filter(id=calendario.id).exists())
