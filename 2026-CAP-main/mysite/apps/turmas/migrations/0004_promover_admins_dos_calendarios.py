from django.db import migrations


def promover_admins_dos_calendarios(apps, schema_editor):
    MembroDeCalendario = apps.get_model('calendarios', 'MembroDeCalendario')
    MembroDeTurma = apps.get_model('turmas', 'MembroDeTurma')
    database = schema_editor.connection.alias

    administradores = MembroDeCalendario.objects.using(database).filter(
        eh_admin=True,
        calendario__turma__isnull=False,
    ).values_list('usuario_id', 'calendario__turma_id').distinct()

    for usuario_id, turma_id in administradores.iterator():
        MembroDeTurma.objects.using(database).filter(
            usuario_id=usuario_id,
            turma_id=turma_id,
        ).update(eh_admin=True)


class Migration(migrations.Migration):

    dependencies = [
        ('calendarios', '0003_initial'),
        ('turmas', '0003_alter_turma_codigo'),
    ]

    operations = [
        migrations.RunPython(promover_admins_dos_calendarios, migrations.RunPython.noop),
    ]
