from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seafood', '0020_create_callbackrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callbackrequest',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
