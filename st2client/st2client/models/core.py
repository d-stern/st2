# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import logging
from functools import wraps

import six

from six.moves import urllib
from st2client.utils import httpclient


LOG = logging.getLogger(__name__)


def add_auth_token_to_kwargs_from_env(func):
    @wraps(func)
    def decorate(*args, **kwargs):
        if not kwargs.get('token') and os.environ.get('ST2_AUTH_TOKEN', None):
            kwargs['token'] = os.environ.get('ST2_AUTH_TOKEN')
        return func(*args, **kwargs)
    return decorate


class Resource(object):

    # An alias to use for the resource if different than the class name.
    _alias = None

    # Display name of the resource. This may be different than its resource
    # name specifically when the resource name is composed of multiple words.
    _display_name = None

    # URL path for the resource.
    _url_path = None

    # Plural form of the resource name. This will be used to build the
    # latter part of the REST URL.
    _plural = None

    # Plural form of the resource display name.
    _plural_display_name = None

    # A list of class attributes which will be included in __repr__ return value
    _repr_attributes = []

    def __init__(self, *args, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

    def to_dict(self, exclude_attributes=None):
        """
        Return a dictionary representation of this object.

        :param exclude_attributes: Optional list of attributes to exclude.
        :type exclude_attributes: ``list``

        :rtype: ``dict``
        """
        exclude_attributes = exclude_attributes or []

        attributes = self.__dict__.keys()
        attributes = [attr for attr in attributes if not attr.startswith('__') and
                      attr not in exclude_attributes]

        result = {}
        for attribute in attributes:
            value = getattr(self, attribute, None)
            result[attribute] = value

        return result

    @classmethod
    def get_alias(cls):
        return cls._alias if cls._alias else cls.__name__

    @classmethod
    def get_display_name(cls):
        return cls._display_name if cls._display_name else cls.__name__

    @classmethod
    def get_plural_name(cls):
        if not cls._plural:
            raise Exception('The %s class is missing class attributes '
                            'in its definition.' % cls.__name__)
        return cls._plural

    @classmethod
    def get_plural_display_name(cls):
        return (cls._plural_display_name
                if cls._plural_display_name
                else cls._plural)

    @classmethod
    def get_url_path_name(cls):
        if cls._url_path:
            return cls._url_path

        return cls.get_plural_name().lower()

    def serialize(self):
        return dict((k, v)
                    for k, v in six.iteritems(self.__dict__)
                    if not k.startswith('_'))

    @classmethod
    def deserialize(cls, doc):
        if type(doc) is not dict:
            doc = json.loads(doc)
        return cls(**doc)

    def __str__(self):
        return str(self.__repr__())

    def __repr__(self):
        if not self._repr_attributes:
            return super(Resource, self).__repr__()

        attributes = []
        for attribute in self._repr_attributes:
            value = getattr(self, attribute, None)
            attributes.append('%s=%s' % (attribute, value))

        attributes = ','.join(attributes)
        class_name = self.__class__.__name__
        result = '<%s %s>' % (class_name, attributes)
        return result


class ResourceManager(object):

    def __init__(self, resource, endpoint, cacert=None, debug=False):
        self.resource = resource
        self.debug = debug
        self.client = httpclient.HTTPClient(endpoint, cacert=cacert, debug=debug)

    @staticmethod
    def handle_error(response):
        try:
            content = response.json()
            fault = content.get('faultstring', '') if content else ''
            if fault:
                response.reason += '\nMESSAGE: %s' % fault
        except Exception as e:
            response.reason += ('\nUnable to retrieve detailed message '
                                'from the HTTP response. %s\n' % str(e))
        response.raise_for_status()

    @add_auth_token_to_kwargs_from_env
    def get_all(self, **kwargs):
        # TODO: This is ugly, stop abusing kwargs
        url = '/%s' % self.resource.get_url_path_name()
        limit = kwargs.pop('limit', None)
        pack = kwargs.pop('pack', None)
        prefix = kwargs.pop('prefix', None)

        params = {}
        if limit and limit <= 0:
            limit = None
        if limit:
            params['limit'] = limit

        if pack:
            params['pack'] = pack

        if prefix:
            params['prefix'] = prefix

        response = self.client.get(url=url, params=params, **kwargs)
        if response.status_code != 200:
            self.handle_error(response)
        return [self.resource.deserialize(item)
                for item in response.json()]

    @add_auth_token_to_kwargs_from_env
    def get_by_id(self, id, **kwargs):
        url = '/%s/%s' % (self.resource.get_url_path_name(), id)
        response = self.client.get(url, **kwargs)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            self.handle_error(response)
        return self.resource.deserialize(response.json())

    @add_auth_token_to_kwargs_from_env
    def get_property(self, id_, property_name, self_deserialize=True, **kwargs):
        """
        Gets a property of a Resource.
        id_ : Id of the resource
        property_name: Name of the property
        self_deserialize: #Implies use the deserialize method implemented by this resource.
        """
        token = None
        if kwargs:
            token = kwargs.pop('token', None)

            url = '/%s/%s/%s/?%s' % (self.resource.get_url_path_name(), id_, property_name,
                                     urllib.parse.urlencode(kwargs))
        else:
            url = '/%s/%s/%s/' % (self.resource.get_url_path_name(), id_, property_name)

        response = self.client.get(url, token=token) if token else self.client.get(url)

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            self.handle_error(response)

        if self_deserialize:
            return [self.resource.deserialize(item) for item in response.json()]
        else:
            return response.json()

    @add_auth_token_to_kwargs_from_env
    def get_by_ref_or_id(self, ref_or_id, **kwargs):
        return self.get_by_id(id=ref_or_id, **kwargs)

    @add_auth_token_to_kwargs_from_env
    def query(self, **kwargs):
        if not kwargs:
            raise Exception('Query parameter is not provided.')
        if 'limit' in kwargs and kwargs.get('limit') <= 0:
            kwargs.pop('limit')
        token = kwargs.get('token', None)
        params = {}
        for k, v in six.iteritems(kwargs):
            if k != 'token':
                params[k] = v
        url = '/%s/?%s' % (self.resource.get_url_path_name(),
                           urllib.parse.urlencode(params))
        response = self.client.get(url, token=token) if token else self.client.get(url)
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            self.handle_error(response)
        items = response.json()
        instances = [self.resource.deserialize(item) for item in items]
        return instances

    @add_auth_token_to_kwargs_from_env
    def get_by_name(self, name_or_id, **kwargs):
        instances = self.query(name=name_or_id, **kwargs)
        if not instances:
            return None
        else:
            if len(instances) > 1:
                raise Exception('More than one %s named "%s" are found.' %
                                (self.resource.__name__.lower(), name_or_id))
            return instances[0]

    @add_auth_token_to_kwargs_from_env
    def create(self, instance, **kwargs):
        url = '/%s' % self.resource.get_url_path_name()
        response = self.client.post(url, instance.serialize(), **kwargs)
        if response.status_code != 200:
            self.handle_error(response)
        instance = self.resource.deserialize(response.json())
        return instance

    @add_auth_token_to_kwargs_from_env
    def update(self, instance, **kwargs):
        url = '/%s/%s' % (self.resource.get_url_path_name(), instance.id)
        response = self.client.put(url, instance.serialize(), **kwargs)
        if response.status_code != 200:
            self.handle_error(response)
        instance = self.resource.deserialize(response.json())
        return instance

    @add_auth_token_to_kwargs_from_env
    def delete(self, instance, **kwargs):
        url = '/%s/%s' % (self.resource.get_url_path_name(), instance.id)
        response = self.client.delete(url, **kwargs)

        if response.status_code not in [200, 204, 404]:
            self.handle_error(response)
            return False

        return True

    @add_auth_token_to_kwargs_from_env
    def delete_by_id(self, instance_id, **kwargs):
        url = '/%s/%s' % (self.resource.get_url_path_name(), instance_id)
        response = self.client.delete(url, **kwargs)
        if response.status_code not in [200, 204, 404]:
            self.handle_error(response)
            return False
        try:
            resp_json = response.json()
            if resp_json:
                return resp_json
        except:
            pass
        return True


class ActionAliasResourceManager(ResourceManager):
    def __init__(self, resource, endpoint, cacert=None, debug=False):
        self.resource = resource
        self.debug = debug
        self.client = httpclient.HTTPClient(root=endpoint, cacert=cacert, debug=debug)


class LiveActionResourceManager(ResourceManager):
    @add_auth_token_to_kwargs_from_env
    def re_run(self, execution_id, parameters=None, **kwargs):
        url = '/%s/%s/re_run' % (self.resource.get_url_path_name(), execution_id)

        data = {}
        if parameters:
            data['parameters'] = parameters

        response = self.client.post(url, data, **kwargs)
        if response.status_code != 200:
            self.handle_error(response)

        instance = self.resource.deserialize(response.json())
        return instance


class TriggerInstanceResourceManager(ResourceManager):
    @add_auth_token_to_kwargs_from_env
    def re_emit(self, trigger_instance_id, **kwargs):
        url = '/%s/%s/re_emit' % (self.resource.get_url_path_name(), trigger_instance_id)
        response = self.client.post(url, None)
        if response.status_code != 200:
            self.handle_error(response)
        return response.json()
