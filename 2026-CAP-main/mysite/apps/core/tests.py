from django.test import TestCase
from django.urls import reverse

from apps.core.management.commands.populate import popular_turmas
from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.turmas.models import MembroDeTurma, Turma
from apps.usuarios.models import Usuario


class PopularTurmasTests(TestCase):
    def test_admins_dos_calendarios_da_turma_recebem_acesso_as_acoes_da_turma(self):
        admin = Usuario.objects.create_user(
            email='carlos@teste.com',
            password='Senha@123',
            nome_completo='Carlos Danilo',
        )
        membro = Usuario.objects.create_user(
            email='andre@teste.com',
            password='Senha@123',
            nome_completo='André Isaque',
        )
        outro_admin = Usuario.objects.create_user(
            email='joao@teste.com',
            password='Senha@123',
            nome_completo='João Gabriel',
        )
        calendario_pessoal = Calendario.objects.create(nome='Calendário pessoal')
        MembroDeCalendario.objects.create(
            usuario=admin,
            calendario=calendario_pessoal,
            eh_admin=True,
            numero_paleta=1,
        )

        popular_turmas([{
            'nome': 'Infoweb 3M',
            'calendarios': [{'nome': 'Calendário antigo'}],
        }])
        turma = Turma.objects.get(nome='Infoweb 3M')

        membros = list(
            MembroDeTurma.objects.filter(turma=turma).order_by('usuario_id').values_list(
                'usuario_id',
                'eh_admin',
            )
        )
        self.assertEqual(
            membros,
            [(admin.id, True), (membro.id, False), (outro_admin.id, True)],
        )

        self.client.force_login(admin)
        response = self.client.get(reverse('turma', args=[turma.id]))

        self.assertContains(response, 'data-id-painel="painel-calendarios"')
        self.assertContains(response, 'Calendários da turma')
        self.assertContains(response, 'Associar calendário')
        self.assertContains(response, 'Criar calendário de turma')
        self.assertContains(response, 'Calendário antigo')
        self.assertContains(response, 'Remover calendário da turma?')
        self.assertContains(response, 'data-abrir-modal="modal-remover-participante-')
