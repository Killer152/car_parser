from django.core.management.base import BaseCommand
from ...models import Fuel, Transmission


class Command(BaseCommand):
    help = 'Creates default Fuel and Transmission types with multilingual support'

    def handle(self, *args, **options):

        fuel_types = [
            {
                'name': 'gasoline',
                'name_ru': 'Бензин',
                'name_kr': '가솔린'
            },
            {
                'name': 'diesel',
                'name_ru': 'Дизель',
                'name_kr': '디젤'
            },
            {
                'name': 'electric',
                'name_ru': 'Электрический',
                'name_kr': '전기'
            },
            {
                'name': 'gasoline+electric',
                'name_ru': 'Бензин+Электричество',
                'name_kr': '가솔린+전기'
            },
            {
                'name': 'diesel+electric',
                'name_ru': 'Дизель+Электричество',
                'name_kr': '디젤+전기'
            },
            {
                'name': 'gasoline+lpg',
                'name_ru': 'Бензин+ГБО',
                'name_kr': '가솔린+LPG'
            },
            {
                'name': 'other',
                'name_ru': 'Другое',
                'name_kr': '기타'
            }
        ]

        transmission_types = [
            {
                'name': 'automatic',
                'name_ru': 'Автоматическая',
                'name_kr': '자동'
            },
            {
                'name': 'mechanical',
                'name_ru': 'Механическая',
                'name_kr': '수동'
            },
            {
                'name': 'semi_automatic',
                'name_ru': 'Полуавтоматическая',
                'name_kr': '반자동'
            },
            {
                'name': 'variator',
                'name_ru': 'Вариатор',
                'name_kr': '무단변속기'
            },
            {
                'name': 'other',
                'name_ru': 'Другое',
                'name_kr': '기타'
            }
        ]

        created_fuels = 0
        updated_fuels = 0
        for fuel_data in fuel_types:
            fuel, created = Fuel.objects.get_or_create(
                name=fuel_data['name'],
                defaults={
                    'name_ru': fuel_data['name_ru'],
                    'name_kr': fuel_data['name_kr']
                }
            )

            if created:
                created_fuels += 1
                self.stdout.write(f"Created fuel type: {fuel_data['name']}")
            else:

                updated = False
                if not fuel.name_ru or fuel.name_ru != fuel_data['name_ru']:
                    fuel.name_ru = fuel_data['name_ru']
                    updated = True
                if not fuel.name_kr or fuel.name_kr != fuel_data['name_kr']:
                    fuel.name_kr = fuel_data['name_kr']
                    updated = True

                if updated:
                    fuel.save()
                    updated_fuels += 1
                    self.stdout.write(f"Updated fuel type: {fuel_data['name']}")
                else:
                    self.stdout.write(f"Fuel type already exists: {fuel_data['name']}")

        created_transmissions = 0
        updated_transmissions = 0
        for transmission_data in transmission_types:
            transmission, created = Transmission.objects.get_or_create(
                name=transmission_data['name'],
                defaults={
                    'name_ru': transmission_data['name_ru'],
                    'name_kr': transmission_data['name_kr']
                }
            )

            if created:
                created_transmissions += 1
                self.stdout.write(f"Created transmission type: {transmission_data['name']}")
            else:

                updated = False
                if not transmission.name_ru or transmission.name_ru != transmission_data['name_ru']:
                    transmission.name_ru = transmission_data['name_ru']
                    updated = True
                if not transmission.name_kr or transmission.name_kr != transmission_data['name_kr']:
                    transmission.name_kr = transmission_data['name_kr']
                    updated = True

                if updated:
                    transmission.save()
                    updated_transmissions += 1
                    self.stdout.write(f"Updated transmission type: {transmission_data['name']}")
                else:
                    self.stdout.write(f"Transmission type already exists: {transmission_data['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {created_fuels} fuel types and {created_transmissions} transmission types. "
            f"Updated {updated_fuels} fuel types and {updated_transmissions} transmission types."
        ))