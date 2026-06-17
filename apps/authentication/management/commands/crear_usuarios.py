from django.core.management.base import BaseCommand
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Crea usuarios demo para el sistema'

    def handle(self, *args, **options):
        usuarios = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'administrador',
                'first_name': 'Admin',
                'last_name': 'Sistema',
                'email': 'admin@healthanalytics.co'
            },
            {
                'username': 'medico',
                'password': 'medico123',
                'role': 'medico',
                'first_name': 'Dr. Juan',
                'last_name': 'Pérez',
                'email': 'medico@healthanalytics.co'
            },
            {
                'username': 'analista',
                'password': 'analista123',
                'role': 'analista',
                'first_name': 'Ana',
                'last_name': 'García',
                'email': 'analista@healthanalytics.co'
            },
        ]

        for u in usuarios:
            if not User.objects.filter(username=u['username']).exists():
                User.objects.create_user(**u)
                self.stdout.write(
                    self.style.SUCCESS(f"  ✔ Usuario creado: {u['username']} / {u['password']}")
                )
            else:
                self.stdout.write(f"  — Ya existe: {u['username']}")

        self.stdout.write(self.style.SUCCESS('\nUsuarios listos.'))