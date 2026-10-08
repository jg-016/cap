from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from apps.calendarios.models import Calendario, MembroDeCalendario
from apps.eventos.models import Evento
from apps.usuarios.models import Usuario


class EventoViewTests(TestCase):
	def setUp(self):
		self.admin = Usuario.objects.create_user(
			email='admin@teste.com',
			password='Senha@123',
			nome_completo='Admin Teste',
		)
		self.membro = Usuario.objects.create_user(
			email='membro@teste.com',
			password='Senha@123',
			nome_completo='Membro Teste',
		)
		self.calendario = Calendario.objects.create(
			nome='Calendário Teste',
			descricao='Descrição do calendário',
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
		self.evento = Evento.objects.create(
			nome='Reunião do grupo',
			conteudo='Planejamento da semana',
			inicio=datetime(2026, 8, 12, 9, 0, 0),
			fim=datetime(2026, 8, 12, 10, 30, 0),
			calendario=self.calendario,
		)

	def test_visualizar_evento_exibe_informacoes(self):
		self.client.force_login(self.admin)

		response = self.client.get(
			reverse('eventos:visualizar_evento', args=[self.evento.id])
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.evento.nome)
		self.assertContains(response, self.evento.conteudo)
		self.assertContains(response, '<dialog')
		self.assertContains(
			response,
			reverse('eventos:deletar_evento', args=[self.evento.id]),
		)

	def test_get_deletar_evento_redireciona_para_detalhes(self):
		self.client.force_login(self.admin)

		response = self.client.get(
			reverse('eventos:deletar_evento', args=[self.evento.id])
		)

		self.assertRedirects(
			response,
			reverse('eventos:visualizar_evento', args=[self.evento.id]),
		)

	def test_deletar_evento_remove_evento_e_redireciona(self):
		self.client.force_login(self.admin)

		response = self.client.post(
			reverse('eventos:deletar_evento', args=[self.evento.id])
		)

		self.assertRedirects(
			response,
			reverse('inicio'),
		)
		self.assertFalse(Evento.objects.filter(id=self.evento.id).exists())

	def test_membro_comum_nao_pode_deletar_evento(self):
		self.client.force_login(self.membro)

		response = self.client.post(
			reverse('eventos:deletar_evento', args=[self.evento.id])
		)

		self.assertRedirects(
			response,
			reverse('eventos:visualizar_evento', args=[self.evento.id]),
		)
		self.assertTrue(Evento.objects.filter(id=self.evento.id).exists())
