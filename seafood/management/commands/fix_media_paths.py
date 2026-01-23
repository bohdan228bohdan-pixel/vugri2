from django.core.management.base import BaseCommand
from django.apps import apps
import os

class Command(BaseCommand):
    help = "Fix FileField/ImageField paths that incorrectly include a leading 'media/' prefix. Run with --dry-run first."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without applying')

    def handle(self, *args, **options):
        dry = options['dry_run']
        from django.conf import settings

        MEDIA_ROOT = os.path.abspath(str(settings.MEDIA_ROOT))
        total_candidates = 0
        total_updates = 0

        for model in apps.get_models():
            model_name = f"{model._meta.app_label}.{model.__name__}"
            qs = model.objects.all()
            for obj in qs:
                changed = False
                for field in [f for f in obj._meta.get_fields() if getattr(f, 'get_internal_type', lambda: None)() in ('FileField','ImageField')]:
                    try:
                        val = getattr(obj, field.name)
                        name = getattr(val, 'name', None)
                        if not name or not isinstance(name, str):
                            continue
                        lower = name.lower()
                        if not any(lower.endswith(ext) for ext in ('.jpg','.jpeg','.png','.webp','.gif')):
                            continue
                        # normalize leading slashes
                        newname = name.lstrip('/')
                        # strip leading 'media/' if present
                        if newname.startswith('media/'):
                            newname = newname[len('media/'):]
                        if newname == name.lstrip('/'):
                            # nothing to change (name had no 'media/' prefix anymore)
                            continue
                        # path where Django will look for file: MEDIA_ROOT/newname
                        target_path = os.path.join(MEDIA_ROOT, newname)
                        if os.path.exists(target_path):
                            total_candidates += 1
                            self.stdout.write(f"Candidate: {model_name} id={getattr(obj,'pk',None)} field={field.name}  {name!r} -> {newname!r} (exists)")
                            if not dry:
                                # assign new relative name to field and save object
                                try:
                                    setattr(obj, field.name, newname)
                                except Exception:
                                    # fallback: try assign string to the descriptor if that fails
                                    try:
                                        getattr(obj, field.name).name = newname
                                    except Exception as e:
                                        self.stderr.write(f"Failed to set {field.name} on {model_name} id={getattr(obj,'pk',None)}: {e}")
                                        continue
                                obj.save()
                                total_updates += 1
                                self.stdout.write(f"Updated: {model_name} id={getattr(obj,'pk',None)}")
                        else:
                            # target file does not exist; report for manual review
                            self.stdout.write(f"Missing target for {model_name} id={getattr(obj,'pk',None)}: would map {name!r} -> {newname!r} but file not found at {target_path}")
                    except Exception as exc:
                        self.stderr.write(f"Error processing {model_name} id={getattr(obj,'pk',None)} field={getattr(field,'name',None)}: {exc}")

        self.stdout.write(self.style.SUCCESS(f"Done. Candidates: {total_candidates}. Updated: {total_updates}. (dry-run={dry})"))