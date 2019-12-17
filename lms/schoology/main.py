from .auth import AuthorizationError
import time
import json

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


class Schoology:
    _ROOT = 'https://api.schoology.com/v1/'
    limit = 20
    start = 0

    def __init__(self, schoology_auth):
        if not schoology_auth.authorized:
            raise AuthorizationError('Auth instance not authorized. Run authorize() after requesting authorization.')
        self.schoology_auth = schoology_auth

    def _get(self, path):
        """
        GET data from a given endpoint.

        :param path: Path (following API root) to endpoint.
        :return: JSON response.
        """
        try:
            response = self.schoology_auth.oauth.get(url='%s%s?limit=%s&start=%s' % (self._ROOT, path, self.limit, self.start), headers=self.schoology_auth._request_header(), auth=self.schoology_auth.oauth.auth)
            return response.json()
        except JSONDecodeError:
            return {}

    def _post(self, path, data):
        """
        POST valid JSON to a given endpoint.

        :param path: Path (following API root) to endpoint.
        :param data: JSON data to POST.
        :return: JSON response.
        """
        try:
            return self.schoology_auth.oauth.post(url='%s%s?limit=%s' % (self._ROOT, path, self.limit), json=data, headers=self.schoology_auth._request_header(), auth=self.schoology_auth.oauth.auth).json()
        except JSONDecodeError:
            return {}

    def _put(self, path, data):
        """
        PUT valid JSON to a given endpoint.

        :param path: Path (following API root) to endpoint.
        :param data: JSON data to PUT.
        :return: JSON response.
        """
        try:
            return self.schoology_auth.oauth.put(url='%s%s?limit=%s' % (self._ROOT, path, self.limit), json=data, headers=self.schoology_auth._request_header(), auth=self.schoology_auth.oauth.auth).json()
        except JSONDecodeError:
            return {}

    def _delete(self, path):
        """
        Send a DELETE request to a given endpoint.

        :param path: Path (following API root) to endpoint.
        """
        return self.schoology_auth.oauth.delete(url='%s%s' % (self._ROOT, path), headers=self.schoology_auth._request_header(), auth=self.schoology_auth.oauth.auth)

    # TODO: Implement multi-get(!) and multi-options requests. Don't seem to work right now.
