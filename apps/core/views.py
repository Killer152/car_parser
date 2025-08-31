import os
from typing import Dict, Optional

import requests
from django.core.cache import cache
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

load_dotenv()


class CarAPIService:

    def __init__(self):
        self.base_url = "https://carapi.app/api"
        self.api_token = os.getenv('CARAPI_TOKEN')
        self.api_secret = os.getenv('CAR_API_SECRET_KEY')
        self.jwt_token = None
        self.jwt_expiry = None

    def get_jwt_token(self) -> Optional[str]:

        cached_token = cache.get('carapi_jwt_token')
        if cached_token:
            return cached_token

        if not self.api_token or not self.api_secret:
            return None

        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "api_token": self.api_token,
                    "api_secret": self.api_secret
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')

                cache.set('carapi_jwt_token', token, 6 * 24 * 60 * 60)

                return token
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error getting JWT token: {e}")
            return None

    def make_request(self, endpoint: str, params: Optional[Dict] = None, use_v2: bool = False) -> Dict:

        headers = {}
        jwt_token = self.get_jwt_token()

        if jwt_token:
            headers['Authorization'] = f'Bearer {jwt_token}'

        headers['Accept'] = 'application/json'

        if use_v2 and not endpoint.endswith('/v2'):
            endpoint = endpoint.rstrip('/') + '/v2'

        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 401:

                cache.delete('carapi_jwt_token')
                jwt_token = self.get_jwt_token()
                if jwt_token:
                    headers['Authorization'] = f'Bearer {jwt_token}'
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        headers=headers,
                        timeout=10
                    )

            if response.status_code == 403 and 'deprecated' in response.text.lower():

                if not endpoint.endswith('/v2'):
                    print(f"Endpoint {endpoint} deprecated, trying v2...")
                    return self.make_request(endpoint, params, use_v2=True)

            return {
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None,
                'error': response.text if response.status_code != 200 else None,
                'raw_response': response
            }

        except requests.exceptions.Timeout:
            return {
                'status_code': 504,
                'data': None,
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'status_code': 500,
                'data': None,
                'error': str(e)
            }


class CarAPIBaseView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = CarAPIService()

    def handle_response(self, result: Dict) -> Response:
        """Convert service response to DRF Response"""
        if result['status_code'] == 200:
            data = result['data']

            if isinstance(data, dict) and 'data' in data:

                return Response({
                    'success': True,
                    'data': data.get('data', []),
                    'collection': data.get('collection', {}),
                    'count': len(data.get('data', []))
                }, status=status.HTTP_200_OK)
            else:

                return Response({
                    'success': True,
                    'data': data if isinstance(data, list) else [data],
                    'count': len(data) if isinstance(data, list) else 1
                }, status=status.HTTP_200_OK)


class GetYearsAPIView(CarAPIBaseView):

    def get(self, request):
        result = self.service.make_request('/years', use_v2=True)
        return self.handle_response(result)


class GetMakesAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        if request.query_params.get('year'):
            params['year'] = request.query_params.get('year')

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        result = self.service.make_request('/makes', params, use_v2=True)
        return self.handle_response(result)


class GetModelsAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        if request.query_params.get('year'):
            params['year'] = request.query_params.get('year')

        if request.query_params.get('make'):
            params['make'] = request.query_params.get('make')

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        result = self.service.make_request('/models', params, use_v2=True)
        return self.handle_response(result)


class GetSubmodelsAPIView(CarAPIBaseView):

    def get(self, request):

        params = {}

        if request.query_params.get('year'):
            params['year'] = request.query_params.get('year')

        if request.query_params.get('make'):
            params['make'] = request.query_params.get('make')

        if request.query_params.get('model'):
            params['model'] = request.query_params.get('model')

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        if request.query_params.get('sort'):
            params['sort'] = request.query_params.get('sort')
            params['direction'] = request.query_params.get('direction', 'asc')

        if request.query_params.get('search'):
            params['search'] = request.query_params.get('search')

        result = self.service.make_request('/submodels', params, use_v2=True)
        return self.handle_response(result)


class GetTrimsAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        for param in ['year', 'make', 'model', 'submodel']:
            if request.query_params.get(param):
                params[param] = request.query_params.get(param)

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        if request.query_params.get('search'):
            params['search'] = request.query_params.get('search')

        result = self.service.make_request('/trims', params, use_v2=True)
        return self.handle_response(result)


class GetBodiesAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        if request.query_params.get('trim_id'):
            params['trim_id'] = request.query_params.get('trim_id')

        for param in ['year', 'make', 'model']:
            if request.query_params.get(param):
                params[param] = request.query_params.get(param)

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        result = self.service.make_request('/bodies', params, use_v2=True)
        return self.handle_response(result)


class GetEnginesAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        if request.query_params.get('trim_id'):
            params['trim_id'] = request.query_params.get('trim_id')

        for param in ['year', 'make', 'model']:
            if request.query_params.get(param):
                params[param] = request.query_params.get(param)

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        result = self.service.make_request('/engines', params, use_v2=True)
        return self.handle_response(result)


class GetMileagesAPIView(CarAPIBaseView):

    def get(self, request):
        params = {}

        if request.query_params.get('trim_id'):
            params['trim_id'] = request.query_params.get('trim_id')

        for param in ['year', 'make', 'model']:
            if request.query_params.get(param):
                params[param] = request.query_params.get(param)

        params['limit'] = request.query_params.get('limit', '100')
        params['page'] = request.query_params.get('page', '1')

        result = self.service.make_request('/mileages', params, use_v2=True)
        return self.handle_response(result)


class VINDecodeAPIView(CarAPIBaseView):

    def get(self, request, vin):
        if len(vin) != 17:
            return Response({
                'success': False,
                'error': 'VIN must be exactly 17 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = self.service.make_request(f'/vin/{vin}')

        return self.handle_response(result)
