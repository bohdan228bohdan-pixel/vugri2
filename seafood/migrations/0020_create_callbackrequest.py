cat > seafood/migrations/0020_create_callbackrequest.py <<'PY'
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('seafood', '0019_seafoodproduct_price_per_unit_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ("name", models.CharField("Ім'я", max_length=120, blank=True)),
                ('phone', models.CharField("Телефон", max_length=40)),
                ('message', models.TextField("Повідомлення", blank=True)),
                ('preferred_time', models.CharField("Зручний час", max_length=80, blank=True)),
                ('created_at', models.DateTimeField("Створено", default=django.utils.timezone.now)),
                ('processed', models.BooleanField("Опрацьовано", default=False)),
                ('product', models.ForeignKey(related_name='callback_requests', null=True, blank=True, to='seafood.SeafoodProduct', on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
                'verbose_name': "Запит зворотного зв'язку",
                'verbose_name_plural': "Запити зворотного зв'язку",
                'ordering': ['-created_at'],
            },
        ),
    ]
PY
