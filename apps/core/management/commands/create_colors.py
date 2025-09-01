import json
import os

from django.core.management.base import BaseCommand

from ...models import Color


class Command(BaseCommand):
    help = 'Create colors from JSON file'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_dir = os.path.join(base_dir, 'excel', 'json')
        file_path = os.path.join(json_dir, 'trans_oprions_all_encar.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.NOTICE(f'Importing colors from {file_path}...'))

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                colors_data = data.get('Color', [])

            colors_created = 0
            colors_updated = 0

            for color_item in colors_data:
                color_data = {
                    'code': color_item.get('Code', '').strip() or None,
                    'name': color_item['name_en'].strip(),
                    'name_ru': color_item['name_ru'].strip(),
                    'name_kr': color_item['name_kr'].strip(),
                    'icon': color_item.get('Code', '').strip() or None
                }

                color, created = Color.objects.update_or_create(
                    code=color_data['code'],
                    defaults=color_data
                )

                if created:
                    colors_created += 1
                    self.stdout.write(f'Created: {color_data["code"]} - {color_data["name"]}')
                else:
                    colors_updated += 1
                    self.stdout.write(f'Updated: {color_data["code"]} - {color_data["name"]}')

            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported colors: {colors_created} created, {colors_updated} updated')
            )

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Error parsing JSON file: {e}'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'Missing key in JSON data: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
