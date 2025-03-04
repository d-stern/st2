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

from st2common.util.enum import Enum

__all__ = [
    'ResourceType'
]


class ResourceType(Enum):
    """
    Enum representing a valid resource type in a system.
    """

    PACK = 'pack'
    ACTION = 'action'
    SENSOR_TYPE = 'sensor_type'
    TRIGGER_TYPE = 'trigger_type'
    TRIGGER = 'trigger'
    TRIGGER_INSTANCE = 'trigger_instance'
    RULE = 'rule'

    EXECUTION = 'execution'
    KEY_VALUE_PAIR = 'key_value_pair'

    WEBHOOK = 'webhook'
    UNKNOWN = 'unknown'
