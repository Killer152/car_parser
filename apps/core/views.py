from os import getenv

import requests
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

load_dotenv()


class CarDataAPIView(APIView):
    """
    APIView to fetch car data from API Ninjas
    """
    permission_classes = [AllowAny]
    def get(self, request):
        params = {
            'limit': request.query_params.get('limit', '1')
        }

        optional_params = [
            'make', 'model', 'fuel_type', 'drive', 'cylinders',
            'transmission', 'year', 'min_city_mpg', 'max_city_mpg',
            'min_hwy_mpg', 'max_hwy_mpg', 'min_comb_mpg', 'max_comb_mpg'
        ]

        for param in optional_params:
            value = request.query_params.get(param)
            if value:
                params[param] = value

        api_url = 'https://api.api-ninjas.com/v1/cars'
        api_key = getenv('HTTP_API_NINJAS_KEY')

        if not api_key:
            return Response(
                {'error': 'API key not configured. Please set API_NINJAS_KEY in settings.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        headers = {
            'X-Api-Key': api_key
        }

        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=10)

            if response.status_code == requests.codes.ok:
                car_data = response.json()

                return Response({
                    'success': True,
                    'count': len(car_data),
                    'data': car_data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': f'External API error: {response.status_code}',
                    'message': response.text
                }, status=status.HTTP_502_BAD_GATEWAY)

        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'Request timeout'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)

        except requests.exceptions.RequestException as e:
            return Response({
                'success': False,
                'error': f'Request failed: {str(e)}'
            }, status=status.HTTP_502_BAD_GATEWAY)

        except Exception as e:
            return Response({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
