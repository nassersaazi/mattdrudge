import os

from django.contrib.auth import get_user_model

User = get_user_model()
pw = os.environ.get("ADMIN_PW", "admin")
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser("admin", "admin@example.com", pw)
    print("Created superuser 'admin'")
else:
    print("Superuser 'admin' already exists")
