# seafood/management/commands/assign_categories.py
from django.core.management.base import BaseCommand
from django.db import transaction
from seafood.models import SeafoodProduct, Category
import re

class Command(BaseCommand):
    help = "Assign products to categories by keyword heuristics."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show proposed assignments without saving')
        parser.add_argument('--force', action='store_true', help='Overwrite existing category assignments')
        parser.add_argument('--create', action='store_true', help='Create missing categories from mapping')

    # mapping: slug -> {'name': human name, 'keywords': [list of keywords]}
    MAPPING = {
        'ikra': {
            'name': 'Ікра',
            'keywords': ['ікр', 'ікра', 'roe', 'caviar']
        },
        'pechinka': {
            'name': 'Печінка тріски',
            'keywords': ['печін', 'печінка', 'liver']
        },
        'crab': {
            'name': "М'ясо краба",
            'keywords': ['краб']
        },
        'krevetky': {
            'name': 'Креветки',
            'keywords': ['крев', 'shrimp', 'prawn']
        },
        'delic': {
            'name': 'Делікатеси',
            'keywords': ['делікат', 'преміум', 'premium', 'деликатес']
        },
        'seafood': {
            'name': 'Морепродукти',
            'keywords': ['морепродукт', 'раки', 'рака', 'молюск', 'риба', 'тунц', 'тунця', 'лосось', 'форел']
        },
    }

    def handle(self, *args, **options):
        dry = options['dry_run']
        force = options['force']
        create = options['create']

        # ensure categories exist (if --create)
        slug_to_cat = {}
        for slug, spec in self.MAPPING.items():
            cat = Category.objects.filter(slug=slug).first()
            if not cat and create:
                cat = Category.objects.create(name=spec['name'], slug=slug)
                self.stdout.write(self.style.SUCCESS(f"Created category: {spec['name']} (slug={slug})"))
            if cat:
                slug_to_cat[slug] = cat

        progs = []
        products = SeafoodProduct.objects.all()
        total = products.count()
        changed = 0
        skipped = 0

        for p in products:
            text = ((p.name or '') + ' ' + (p.description or '')).lower()
            matched_slug = None
            # first-match priority: mapping order above
            for slug, spec in self.MAPPING.items():
                for kw in spec['keywords']:
                    if kw in text:
                        matched_slug = slug
                        break
                if matched_slug:
                    break

            if not matched_slug:
                skipped += 1
                continue

            # get or create category if needed
            cat = slug_to_cat.get(matched_slug)
            if not cat:
                # try find existing by slug or name
                cat = Category.objects.filter(slug=matched_slug).first() or Category.objects.filter(name__iexact=self.MAPPING[matched_slug]['name']).first()
                if not cat and create:
                    cat = Category.objects.create(name=self.MAPPING[matched_slug]['name'], slug=matched_slug)
                    self.stdout.write(self.style.SUCCESS(f"Created category: {cat.name}"))
                if cat:
                    slug_to_cat[matched_slug] = cat

            if not cat:
                # cannot assign because category missing and --create not set
                self.stdout.write(self.style.WARNING(f"Category for slug '{matched_slug}' not found; run with --create to auto-create. Skipping product id={p.id} name='{p.name}'"))
                skipped += 1
                continue

            if p.category and not force:
                # already assigned
                skipped += 1
                continue

            if dry:
                self.stdout.write(f"DRY: would assign product id={p.id} '{p.name}' -> category '{cat.name}'")
            else:
                with transaction.atomic():
                    p.category = cat
                    p.save(update_fields=['category'])
                changed += 1
                self.stdout.write(self.style.SUCCESS(f"Assigned product id={p.id} '{p.name}' -> category '{cat.name}'"))

        self.stdout.write(self.style.NOTICE(f"Done. total={total} changed={changed} skipped={skipped}"))
        if dry:
            self.stdout.write(self.style.WARNING("Dry run — no DB changes made."))