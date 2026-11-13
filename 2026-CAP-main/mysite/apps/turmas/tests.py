from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.turmas.models import MembroDeTurma, Turma
from apps.usuarios.models import Usuario


class PromoverAdminsDosCalendariosMigrationTests(TransactionTestCase):
    migrate_from = [
        ('calendarios', '0003_initial'),
        ('turmas', '0003_alter_turma_codigo'),
    ]
    migrate_to = [
        ('calendarios', '0003_initial'),
        ('turmas', '0004_promover_admins_dos_calendarios'),
    ]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        UsuarioAntigo = old_apps.get_model('usuarios', 'Usuario')
        TurmaAntiga = old_apps.get_model('turmas', 'Turma')
        MembroDeTurmaAntigo = old_apps.get_model('turmas', 'MembroDeTurma')
        CalendarioAntigo = old_apps.get_model('calendarios', 'Calendario')
        MembroDeCalendarioAntigo = old_apps.get_model('calendarios', 'MembroDeCalendario')

        admin = UsuarioAntigo.objects.create(
            email='admin-legado@teste.com',
            nome_completo='Admin Legado',
            password='!',
        )
        membro = UsuarioAntigo.objects.create(
            email='membro-legado@teste.com',
            nome_completo='Membro Legado',
            password='!',
        )
        turma = TurmaAntiga.objects.create(
            nome='Infoweb 3M',
            descricao='',
            codigo='old123',
        )
        MembroDeTurmaAntigo.objects.create(
            usuario=admin,
            turma=turma,
            eh_admin=False,
            numero_paleta=1,
        )
        MembroDeTurmaAntigo.objects.create(
            usuario=membro,
            turma=turma,
            eh_admin=False,
            numero_paleta=2,
        )
        calendario = CalendarioAntigo.objects.create(
            nome='Calendário legado',
            descricao='',
            turma=turma,
        )
        MembroDeCalendarioAntigo.objects.create(
            usuario=admin,
            calendario=calendario,
            eh_admin=True,
            numero_paleta=1,
        )
        MembroDeCalendarioAntigo.objects.create(
            usuario=membro,
            calendario=calendario,
            eh_admin=False,
            numero_paleta=2,
        )

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps_after_migration = executor.loader.project_state(self.migrate_to).apps
        self.admin_id = admin.id
        self.membro_id = membro.id
        self.turma_id = turma.id

    def tearDown(self):
        MigrationExecutor(connection).migrate(self.migrate_to)
        super().tearDown()

    def test_promove_admin_de_calendario_sem_promover_membros_comuns(self):
        MembroDeTurmaAtual = self.apps_after_migration.get_model('turmas', 'MembroDeTurma')

        self.assertTrue(
            MembroDeTurmaAtual.objects.get(
                turma_id=self.turma_id,
                usuario_id=self.admin_id,
            ).eh_admin
        )
        self.assertFalse(
            MembroDeTurmaAtual.objects.get(
                turma_id=self.turma_id,
                usuario_id=self.membro_id,
            ).eh_admin
        )


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


class RemoverParticipanteTurmaTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            email='admin-remocao@teste.com',
            password='Senha@123',
            nome_completo='Administrador da Turma',
        )
        self.membro = Usuario.objects.create_user(
            email='membro-remocao@teste.com',
            password='Senha@123',
            nome_completo='Membro da Turma',
        )
        self.turma = Turma.objects.create(
            nome='Turma para remoção',
            descricao='Descrição da turma',
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

    def test_administrador_remove_membro_e_revoga_acesso_ao_calendario_da_turma(self):
        calendario_turma = Calendario.objects.create(
            nome='Calendário da turma',
            turma=self.turma,
        )
        calendario_pessoal = Calendario.objects.create(
            nome='Calendário pessoal',
        )
        MembroDeCalendario.objects.create(
            usuario=self.membro,
            calendario=calendario_turma,
            eh_admin=False,
            numero_paleta=3,
        )
        MembroDeCalendario.objects.create(
            usuario=self.membro,
            calendario=calendario_pessoal,
            eh_admin=True,
            numero_paleta=4,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('remover_participante_turma', args=[self.turma.id, self.membro.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertFalse(
            MembroDeTurma.objects.filter(usuario=self.membro, turma=self.turma).exists()
        )
        self.assertFalse(
            MembroDeCalendario.objects.filter(
                usuario=self.membro,
                calendario=calendario_turma,
            ).exists()
        )
        self.assertTrue(
            MembroDeCalendario.objects.filter(
                usuario=self.membro,
                calendario=calendario_pessoal,
            ).exists()
        )

    def test_membro_removido_nao_acessa_mais_a_pagina_da_turma(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse('remover_participante_turma', args=[self.turma.id, self.membro.id]),
        )

        self.client.force_login(self.membro)
        response = self.client.get(reverse('turma', args=[self.turma.id]))

        self.assertEqual(response.status_code, 404)

    def test_administrador_nao_pode_remover_a_si_mesmo(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('remover_participante_turma', args=[self.turma.id, self.admin.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertTrue(
            MembroDeTurma.objects.filter(usuario=self.admin, turma=self.turma).exists()
        )
        self.assertContains(response, 'não pode remover a si mesmo')

    def test_administrador_nao_pode_remover_outro_administrador(self):
        outro_admin = Usuario.objects.create_user(
            email='outro-admin-remocao@teste.com',
            password='Senha@123',
            nome_completo='Outro Administrador',
        )
        MembroDeTurma.objects.create(
            usuario=outro_admin,
            turma=self.turma,
            eh_admin=True,
            numero_paleta=3,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('remover_participante_turma', args=[self.turma.id, outro_admin.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertTrue(
            MembroDeTurma.objects.filter(usuario=outro_admin, turma=self.turma).exists()
        )
        self.assertContains(response, 'não podem remover outros administradores')

    def test_membro_comum_nao_pode_remover_participante(self):
        self.client.force_login(self.membro)

        response = self.client.post(
            reverse('remover_participante_turma', args=[self.turma.id, self.admin.id]),
            follow=True,
        )

        self.assertRedirects(response, reverse('turma', args=[self.turma.id]))
        self.assertTrue(
            MembroDeTurma.objects.filter(usuario=self.admin, turma=self.turma).exists()
        )

    def test_pagina_da_turma_exibe_botoes_de_remocao_para_administradores(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('turma', args=[self.turma.id]))

        self.assertContains(response, 'data-id-painel="painel-membros">Membros</li>')
        self.assertContains(response, 'id="painel-membros" class="oculto"')
        self.assertContains(response, '<ul class="lista-membros">', count=1)
        self.assertNotContains(response, '<h2>Administradores</h2>')
        self.assertNotContains(response, '<h2>Alunos</h2>')
        self.assertContains(response, 'data-abrir-modal="modal-remover-participante-')
        self.assertContains(response, 'Remover participante?')
        self.assertNotContains(response, f'aria-label="Remover participante Administrador da Turma"')

    def test_participante_nao_ve_botoes_de_remocao(self):
        self.client.force_login(self.membro)

        response = self.client.get(reverse('turma', args=[self.turma.id]))

        self.assertNotContains(response, 'data-abrir-modal="modal-remover-participante-')

    def test_pagina_de_calendario_nao_exibe_opcao_de_remover_participante(self):
        calendario = Calendario.objects.create(
            nome='Calendário da turma',
            turma=self.turma,
        )
        MembroDeCalendario.objects.create(
            usuario=self.admin,
            calendario=calendario,
            eh_admin=True,
            numero_paleta=1,
        )
        MembroDeCalendario.objects.create(
            usuario=self.membro,
            calendario=calendario,
            eh_admin=False,
            numero_paleta=2,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('calendario', args=[calendario.id]))

        self.assertContains(response, 'data-id-painel="painel-membros">Membros</li>')
        self.assertNotContains(response, 'data-abrir-modal="modal-remover-participante-')
        self.assertNotContains(response, 'Remover participante?')
