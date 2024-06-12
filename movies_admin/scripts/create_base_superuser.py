from django.contrib.auth.models import User

try:
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
except Exception: 
    print("Походу суперюзер уже создан...")
