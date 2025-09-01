import decimal
import logging
import time
from decimal import Decimal
from typing import Dict, Optional

import requests
from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import (
    Stamp, Model, Fuel, Transmission, CarGeneralInfo
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import vehicle data from OpenDataSoft API by make to bypass 10k limit'

    BASE_URL = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/all-vehicles-model/records"
    LIMIT_PER_REQUEST = 100

    MAKES_LIST = [
        ('Chevrolet', 4420),
        ('Ford', 3821),
        ('GMC', 2777),
        ('Dodge', 2690),
        ('BMW', 2469),
        ('Toyota', 2440),
        ('Mercedes-Benz', 1914),
        ('Nissan', 1663),
        ('Porsche', 1469),
        ('Volkswagen', 1313),
        ('Audi', 1271),
        ('Honda', 1183),
        ('Mitsubishi', 1131),
        ('Mazda', 1111),
        ('Jeep', 1109),
        ('Subaru', 1004),
        ('Hyundai', 991),
        ('Volvo', 914),
        ('Pontiac', 893),
        ('Kia', 801),
        ('Chrysler', 759),
        ('Cadillac', 754),
        ('Buick', 716),
        ('Lexus', 694),
        ('Mercury', 609),
        ('Jaguar', 540),
        ('MINI', 530),
        ('Plymouth', 526),
        ('Suzuki', 515),
        ('Infiniti', 477),
        ('Oldsmobile', 462),
        ('Isuzu', 434),
        ('Saab', 432),
        ('Lincoln', 420),
        ('Acura', 415),
        ('Land Rover', 340),
        ('Saturn', 278),
        ('Ferrari', 275),
        ('Rolls-Royce', 232),
        ('Maserati', 209),
        ('Aston Martin', 183),
        ('Bentley', 174),
        ('Eagle', 161),
        ('Lamborghini', 161),
        ('Ram', 157),
        ('Geo', 147),
        ('Tesla', 144),
        ('Genesis', 123),
        ('Peugeot', 98),
        ('Alfa Romeo', 94),
        ('Scion', 84),
        ('Fiat', 80),
        ('Roush Performance', 69),
        ('Daewoo', 67),
        ('Rivian', 67),
        ('Lotus', 66),
        ('Renault', 56),
        ('McLaren Automotive', 48),
        ('smart', 38),
        ('J.K. Motors', 36),
        ('Wallace Environmental', 32),
        ('Maybach', 31),
        ('American Motors Corporation', 27),
        ('Lucid', 24),
        ('Bugatti', 21),
        ('Hummer', 19),
        ('CX Automotive', 17),
        ('Daihatsu', 17),
        ('Federal Coach', 14),
        ('Merkur', 14),
        ('Polestar', 14),
        ('Import Trade Services', 13),
        ('Spyker', 13),
        ('Sterling', 12),
        ('Dabryan Coach Builders Inc', 9),
        ('Yugo', 8),
        ('BYD', 7),
        ('Bertone', 7),
        ('AM General', 6),
        ('Mcevoy Motors', 6),
        ('Pininfarina', 6),
        ('Tecstar, LP', 6),
        ('Bitter Gmbh and Co. Kg', 5),
        ('Karma', 5),
        ('Pagani', 5),
        ('Saleen', 5),
        ('Saleen Performance', 5),
        ('VPG', 5),
        ('Autokraft Limited', 4),
        ('Bill Dovell Motor Car Company', 4),
        ('Grumman Olson', 4),
        ('INEOS Automotive', 4),
        ('Kenyon Corporation Of America', 4),
        ('Mobility Ventures LLC', 4),
        ('Panther Car Company Limited', 4),
        ('RUF Automobile', 4),
        ('TVR Engineering Ltd', 4),
        ('Texas Coach Company', 4),
        ('Vector', 4),
        ('Vinfast', 4),
        ('BMW Alpina', 3),
        ('Consulier Industries Inc', 3),
        ('Dacia', 3),
        ('Evans Automobiles', 3),
        ('Koenigsegg', 3),
        ('Morgan', 3),
        ('Ruf Automobile Gmbh', 3),
        ('Avanti Motor Corporation', 2),
        ('CCC Engineering', 2),
        ('CODA Automotive', 2),
        ('Fisker', 2),
        ('Laforza Automobile Inc', 2),
        ('PAS Inc - GMC', 2),
        ('PAS, Inc', 2),
        ('Quantum Technologies', 2),
        ('Red Shift Ltd.', 2),
        ('SRT', 2),
        ('ASC Incorporated', 1),
        ('Aurora Cars Ltd', 1),
        ('Azure Dynamics', 1),
        ('E. P. Dutton, Inc.', 1),
        ('Environmental Rsch and Devp Corp', 1),
        ('Excalibur Autos', 1),
        ('General Motors', 1),
        ('Goldacre', 1),
        ('Grumman Allied Industries', 1),
        ('Import Foreign Auto Sales Inc', 1),
        ('Isis Imports Ltd', 1),
        ('JBA Motorcars, Inc.', 1),
        ('Kandi', 1),
        ('Lambda Control Systems', 1),
        ('London Coach Co Inc', 1),
        ('London Taxi', 1),
        ('Lordstown', 1),
        ('Mahindra', 1),
        ('Panos', 1),
        ('Panoz Auto-Development', 1),
        ('Qvale', 1),
        ('S and S Coach Company E.p. Dutton', 1),
        ('STI', 1),
        ('Shelby', 1),
        ('Superior Coaches Div E.p. Dutton', 1),
        ('Vixen Motor Company', 1),
        ('Volga Associated Automobile', 1),
    ]

    def __init__(self):
        super().__init__()
        self.cache = {
            'stamps': {},
            'models': {},
            'fuels': {},
            'transmissions': {},
        }
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'makes_processed': 0,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--makes',
            nargs='+',
            type=str,
            help='Specific makes to import (e.g., --makes Toyota Honda BMW)'
        )
        parser.add_argument(
            '--skip-makes',
            type=int,
            default=0,
            help='Number of makes to skip from the beginning of the list'
        )
        parser.add_argument(
            '--limit-makes',
            type=int,
            default=None,
            help='Maximum number of makes to process'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )

    def get_drive_type(self, drive_str: str) -> Optional[str]:
        """Map API drive string to model choices."""
        if not drive_str:
            return None

        drive_lower = drive_str.lower()

        if 'front' in drive_lower:
            return 'fwd'
        elif 'rear' in drive_lower:
            return 'rwd'
        elif '4-wheel' in drive_lower or '4wd' in drive_lower:
            return '4wd'
        elif 'all-wheel' in drive_lower or 'awd' in drive_lower:
            return 'awd'

        return None

    def get_body_type(self, vclass: str, model_name: str = '') -> Optional[str]:
        """Map vehicle class to body type."""
        if not vclass:
            return None

        vclass_lower = vclass.lower()
        model_lower = model_name.lower()

        if 'sedan' in model_lower:
            return 'SEDAN'
        elif 'coupe' in model_lower:
            return 'COUPE'
        elif 'convertible' in model_lower or 'cabriolet' in model_lower:
            return 'CONVERTIBLE'
        elif 'wagon' in model_lower:
            return 'WAGON'

        if 'pickup' in vclass_lower or 'truck' in vclass_lower:
            return 'PICKUP'
        elif 'van' in vclass_lower or 'minivan' in vclass_lower:
            return 'VAN'
        elif 'suv' in vclass_lower or 'sport utility' in vclass_lower or 'special purpose' in vclass_lower:
            return 'SUV'
        elif 'wagon' in vclass_lower:
            return 'WAGON'
        elif 'compact' in vclass_lower or 'subcompact' in vclass_lower:
            return 'HATCHBACK'
        elif 'two seater' in vclass_lower or 'coupe' in vclass_lower:
            return 'COUPE'
        elif 'sedan' in vclass_lower or 'midsize' in vclass_lower or 'large car' in vclass_lower:
            return 'SEDAN'

        return None

    def get_or_create_stamp(self, make_name: str) -> Optional[Stamp]:
        """Get or create a Stamp (manufacturer) instance."""
        if not make_name:
            return None

        if make_name in self.cache['stamps']:
            return self.cache['stamps'][make_name]

        stamp, created = Stamp.objects.get_or_create(
            name=make_name,
            defaults={
                'name_ru': make_name,
                'name_kr': make_name,
            }
        )

        self.cache['stamps'][make_name] = stamp
        if created:
            self.stdout.write(f"Created new stamp: {make_name}")

        return stamp

    def get_or_create_model(self, model_name: str, stamp: Stamp) -> Optional[Model]:
        """Get or create a Model instance."""
        if not model_name or not stamp:
            return None

        clean_name = model_name
        for suffix in ['2WD', '4WD', 'AWD', 'FWD', 'RWD']:
            clean_name = clean_name.replace(suffix, '').strip()

        base_model = clean_name.split()[0] if clean_name else model_name

        cache_key = f"{stamp.id}:{base_model}"
        if cache_key in self.cache['models']:
            return self.cache['models'][cache_key]

        model, created = Model.objects.get_or_create(
            name=base_model,
            stamp=stamp,
            defaults={
                'name_ru': base_model,
                'name_kr': base_model,
            }
        )

        self.cache['models'][cache_key] = model
        if created:
            self.stdout.write(f"Created new model: {base_model} for {stamp.name}")

        return model

    def get_fuel_type(self, fuel_str: str) -> Optional[Fuel]:
        """Map API fuel type to existing Fuel objects."""
        if not fuel_str:
            return None

        if fuel_str in self.cache['fuels']:
            return self.cache['fuels'][fuel_str]

        fuel_lower = fuel_str.lower()

        fuel_name = None
        if 'electric' in fuel_lower and 'gasoline' in fuel_lower:
            fuel_name = 'gasoline+electric'
        elif 'electric' in fuel_lower and 'diesel' in fuel_lower:
            fuel_name = 'diesel+electric'
        elif 'lpg' in fuel_lower and 'gasoline' in fuel_lower:
            fuel_name = 'gasoline+lpg'
        elif 'electric' in fuel_lower:
            fuel_name = 'electric'
        elif 'diesel' in fuel_lower:
            fuel_name = 'diesel'
        elif 'gasoline' in fuel_lower or 'regular' in fuel_lower or 'premium' in fuel_lower or 'midgrade' in fuel_lower:
            fuel_name = 'gasoline'
        elif 'e85' in fuel_lower or 'ethanol' in fuel_lower:
            fuel_name = 'other'
        elif 'hydrogen' in fuel_lower or 'natural gas' in fuel_lower:
            fuel_name = 'other'
        else:
            fuel_name = 'other'

        try:
            fuel = Fuel.objects.get(name=fuel_name)
            self.cache['fuels'][fuel_str] = fuel
            return fuel
        except Fuel.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Fuel type '{fuel_name}' not found in database"))
            return None

    def get_transmission_type(self, trans_str: str) -> Optional[Transmission]:
        """Map API transmission to existing Transmission objects."""
        if not trans_str:
            return None

        if trans_str in self.cache['transmissions']:
            return self.cache['transmissions'][trans_str]

        trans_lower = trans_str.lower()

        trans_name = None
        if 'automatic' in trans_lower or 'auto' in trans_lower:
            trans_name = 'automatic'
        elif 'manual' in trans_lower:
            trans_name = 'mechanical'
        elif 'cvt' in trans_lower or 'variable' in trans_lower or 'variator' in trans_lower:
            trans_name = 'variator'
        elif 'semi' in trans_lower or 'automated' in trans_lower or 'amt' in trans_lower:
            trans_name = 'semi_automatic'
        elif 'dual' in trans_lower or 'dct' in trans_lower:
            trans_name = 'semi_automatic'
        else:
            trans_name = 'other'

        try:
            transmission = Transmission.objects.get(name=trans_name)
            self.cache['transmissions'][trans_str] = transmission
            return transmission
        except Transmission.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Transmission type '{trans_name}' not found in database"))
            return None

    def process_vehicle_record(self, api_data: Dict) -> bool:
        """Process a single vehicle record from the API."""
        try:

            make_name = api_data.get('make')
            model_name = api_data.get('model')
            base_model_name = api_data.get('basemodel', model_name)
            year_str = api_data.get('year')

            if not make_name or not model_name or not year_str:
                self.stats['skipped'] += 1
                return False

            try:
                year = int(year_str)
                if year < 1900 or year > 2030:
                    self.stats['skipped'] += 1
                    return False
            except (ValueError, TypeError):
                self.stats['skipped'] += 1
                return False

            stamp = self.get_or_create_stamp(make_name)
            if not stamp:
                self.stats['skipped'] += 1
                return False

            model = self.get_or_create_model(base_model_name, stamp)
            if not model:
                self.stats['skipped'] += 1
                return False

            fuel = self.get_fuel_type(api_data.get('fueltype1', ''))
            if not fuel:

                fuel = Fuel.objects.filter(name='gasoline').first()
                if not fuel:
                    self.stats['skipped'] += 1
                    return False

            transmission = self.get_transmission_type(api_data.get('trany', ''))
            if not transmission:

                transmission = Transmission.objects.filter(name='automatic').first()
                if not transmission:
                    self.stats['skipped'] += 1
                    return False

            try:
                displ_value = api_data.get('displ', 0)

                if displ_value is None or displ_value == '':
                    engine_volume = None
                else:

                    displ_str = str(displ_value).strip()
                    if not displ_str or displ_str == 'None':
                        engine_volume = None
                    else:
                        engine_volume = Decimal(displ_str)
                        if engine_volume <= 0:
                            engine_volume = None
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                logger.warning(f"Invalid engine displacement value: {api_data.get('displ')} - setting to null")
                engine_volume = None

            drive = self.get_drive_type(api_data.get('drive', ''))
            body_type = self.get_body_type(api_data.get('vclass', ''), model_name)

            vclass = api_data.get('vclass', '').lower()
            if 'two seater' in vclass:
                seats_count = 2
            elif 'van' in vclass or 'minivan' in vclass:
                seats_count = 7
            elif 'pickup' in vclass and 'crew' in model_name.lower():
                seats_count = 5
            elif 'suv' in vclass or 'sport utility' in vclass:
                seats_count = 5
            else:
                seats_count = 4

            external_id = f"opendatasoft_{api_data.get('id', '')}"

            car, created = CarGeneralInfo.objects.update_or_create(
                external_id=external_id,
                defaults={
                    'stamp': stamp,
                    'model': model,
                    'year': year,
                    'engine_volume': engine_volume,
                    'body_type': body_type,
                    'drive': drive,
                    'primary_fuel_type': fuel,
                    'primary_transmission': transmission,
                    'seats_count': seats_count,

                    'generation': None,
                    'horse_power': None,
                    'salon_color': None,
                    'salon_type': None,
                    'primary_color': None,
                    'vin': None,
                    'features': {},
                }
            )

            action = "Created" if created else "Updated"
            logger.debug(
                f"{action}: {stamp.name} {model.name} ({year}) - "
                f"{engine_volume}L {fuel.name} {transmission.name}"
            )

            return True

        except Exception as e:
            logger.error(f"Error processing record: {e}")
            logger.error(f"Failed record: {api_data}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def fetch_vehicles_by_make(self, make_name: str, expected_count: int) -> int:
        """Fetch all vehicles for a specific make."""
        offset = 0
        make_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
        }

        self.stdout.write(f"\nProcessing {make_name} (expected: {expected_count} vehicles)")

        while True:
            try:

                params = {
                    'limit': self.LIMIT_PER_REQUEST,
                    'offset': offset,
                    'refine': f'make:"{make_name}"'
                }

                logger.debug(f"Fetching {make_name}: offset={offset}, limit={self.LIMIT_PER_REQUEST}")
                response = requests.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                total_for_make = data.get('total_count', 0)
                records = data.get('results', [])

                if not records:
                    break

                with transaction.atomic():
                    for record in records:
                        make_stats['processed'] += 1
                        self.stats['total_processed'] += 1

                        if self.process_vehicle_record(record):
                            make_stats['successful'] += 1
                            self.stats['successful'] += 1
                        else:
                            make_stats['failed'] += 1
                            self.stats['failed'] += 1

                if make_stats['processed'] % 100 == 0 or make_stats['processed'] == total_for_make:
                    self.stdout.write(
                        f"  {make_name}: {make_stats['processed']}/{total_for_make} "
                        f"(Success: {make_stats['successful']}, Failed: {make_stats['failed']})"
                    )

                offset += self.LIMIT_PER_REQUEST

                time.sleep(0.2)

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"API request failed for {make_name}: {e}"))
                time.sleep(5)
                continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {make_name}: {e}"))
                break

        self.stdout.write(
            self.style.SUCCESS(
                f"✓ {make_name} complete: {make_stats['successful']} imported, "
                f"{make_stats['failed']} failed"
            )
        )

        return make_stats['successful']

    def handle(self, *args, **options):

        log_level = logging.DEBUG if options['verbose'] else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.stdout.write(self.style.WARNING(
            'Make sure to run "python manage.py create_fuel_transmission" first!'
        ))

        if not Fuel.objects.exists() or not Transmission.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    'No Fuel or Transmission types found. Please run create_fuel_transmission command first.'
                )
            )
            return

        self.stdout.write(self.style.SUCCESS('Starting vehicle data import by make...'))

        if options['makes']:

            makes_to_process = []
            for make_name in options['makes']:

                found = False
                for make, count in self.MAKES_LIST:
                    if make.lower() == make_name.lower():
                        makes_to_process.append((make, count))
                        found = True
                        break
                if not found:
                    self.stdout.write(self.style.WARNING(f"Make '{make_name}' not found in list"))
        else:

            start_idx = options['skip_makes']
            end_idx = start_idx + options['limit_makes'] if options['limit_makes'] else len(self.MAKES_LIST)
            makes_to_process = self.MAKES_LIST[start_idx:end_idx]

        if not makes_to_process:
            self.stdout.write(self.style.ERROR("No makes to process"))
            return

        total_expected = sum(count for _, count in makes_to_process)
        self.stdout.write(
            f"Will process {len(makes_to_process)} makes with approximately {total_expected} vehicles"
        )

        start_time = time.time()

        try:
            for make_name, expected_count in makes_to_process:
                self.stats['makes_processed'] += 1
                self.fetch_vehicles_by_make(make_name, expected_count)

                self.stdout.write(
                    f"Overall progress: {self.stats['makes_processed']}/{len(makes_to_process)} makes, "
                    f"{self.stats['total_processed']} vehicles processed"
                )

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nImport interrupted by user"))

        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Import Summary:"))
        self.stdout.write(f"Makes processed: {self.stats['makes_processed']}/{len(makes_to_process)}")
        self.stdout.write(f"Total vehicles processed: {self.stats['total_processed']}")
        self.stdout.write(f"Successfully imported: {self.stats['successful']}")
        self.stdout.write(f"Failed: {self.stats['failed']}")
        self.stdout.write(f"Skipped (invalid data): {self.stats['skipped']}")
        self.stdout.write(f"Total runtime: {int(hours)}h {int(minutes)}m {int(seconds)}s")
        self.stdout.write("=" * 60)
