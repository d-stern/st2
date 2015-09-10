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

import mock
import six
import yaml
from mistralclient.api.v2 import workbooks
from mistralclient.api.v2 import workflows

from st2tests import config as test_config
test_config.parse_args()

from st2tests import DbTestCase
from st2tests.fixturesloader import FixturesLoader
from st2common.exceptions.workflow import WorkflowDefinitionException
from st2common.models.api.action import ActionAPI, RunnerTypeAPI
from st2common.persistence.action import Action
from st2common.persistence.runner import RunnerType
from st2common.validators.workflow.mistral import v2 as wf_validation_utils


WB_PRE_XFORM_FILE = 'wb_pre_xform.yaml'
WB_POST_XFORM_FILE = 'wb_post_xform.yaml'
WB_INVALID_SYNTAX_FILE = 'wb_invalid_syntax.yaml'
WB_INVALID_YAQL_FILE = 'wb_invalid_yaql.yaml'
WF_PRE_XFORM_FILE = 'wf_pre_xform.yaml'
WF_POST_XFORM_FILE = 'wf_post_xform.yaml'
WF_NO_REQ_PARAM_FILE = 'wf_missing_required_param.yaml'
WF_UNEXP_PARAM_FILE = 'wf_has_unexpected_param.yaml'
WF_INVALID_SYNTAX_FILE = 'wf_invalid_syntax.yaml'
WF_INVALID_YAQL_FILE = 'wf_invalid_yaql.yaml'

TEST_FIXTURES = {
    'workflows': [
        WB_PRE_XFORM_FILE,
        WB_POST_XFORM_FILE,
        WB_INVALID_SYNTAX_FILE,
        WB_INVALID_YAQL_FILE,
        WF_PRE_XFORM_FILE,
        WF_POST_XFORM_FILE,
        WF_NO_REQ_PARAM_FILE,
        WF_UNEXP_PARAM_FILE,
        WF_INVALID_SYNTAX_FILE,
        WF_INVALID_YAQL_FILE
    ],
    'actions': [
        'local.yaml',
        'a1.yaml',
        'a2.yaml',
        'action1.yaml'
    ],
    'runners': [
        'run-local.yaml',
        'testrunner1.yaml',
        'testrunner2.yaml'
    ]
}

PACK = 'generic'
LOADER = FixturesLoader()
FIXTURES = LOADER.load_fixtures(fixtures_pack=PACK, fixtures_dict=TEST_FIXTURES)
WB_PRE_XFORM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WB_PRE_XFORM_FILE)
WB_PRE_XFORM_DEF = FIXTURES['workflows'][WB_PRE_XFORM_FILE]
WB_POST_XFORM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WB_POST_XFORM_FILE)
WB_POST_XFORM_DEF = FIXTURES['workflows'][WB_POST_XFORM_FILE]
WB_INVALID_SYNTAX_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WB_INVALID_SYNTAX_FILE)
WB_INVALID_SYNTAX_DEF = FIXTURES['workflows'][WB_INVALID_SYNTAX_FILE]
WB_INVALID_YAQL_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WB_INVALID_YAQL_FILE)
WB_INVALID_YAQL_DEF = FIXTURES['workflows'][WB_INVALID_YAQL_FILE]
WF_PRE_XFORM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_PRE_XFORM_FILE)
WF_PRE_XFORM_DEF = FIXTURES['workflows'][WF_PRE_XFORM_FILE]
WF_POST_XFORM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_POST_XFORM_FILE)
WF_POST_XFORM_DEF = FIXTURES['workflows'][WF_POST_XFORM_FILE]
WF_NO_REQ_PARAM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_NO_REQ_PARAM_FILE)
WF_NO_REQ_PARAM_DEF = FIXTURES['workflows'][WF_NO_REQ_PARAM_FILE]
WF_UNEXP_PARAM_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_UNEXP_PARAM_FILE)
WF_UNEXP_PARAM_DEF = FIXTURES['workflows'][WF_UNEXP_PARAM_FILE]
WF_INVALID_SYNTAX_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_INVALID_SYNTAX_FILE)
WF_INVALID_SYNTAX_DEF = FIXTURES['workflows'][WF_INVALID_SYNTAX_FILE]
WF_INVALID_YAQL_PATH = LOADER.get_fixture_file_path_abs(PACK, 'workflows', WF_INVALID_YAQL_FILE)
WF_INVALID_YAQL_DEF = FIXTURES['workflows'][WF_INVALID_YAQL_FILE]


class MistralValidationTest(DbTestCase):

    @classmethod
    def setUpClass(cls):
        super(MistralValidationTest, cls).setUpClass()

        for _, fixture in six.iteritems(FIXTURES['runners']):
            instance = RunnerTypeAPI(**fixture)
            RunnerType.add_or_update(RunnerTypeAPI.to_model(instance))

        for _, fixture in six.iteritems(FIXTURES['actions']):
            instance = ActionAPI(**fixture)
            Action.add_or_update(ActionAPI.to_model(instance))

        cls.validator = wf_validation_utils.get_validator()

    def _read_file_content(self, path):
        with open(path, 'r') as f:
            return f.read()

    def _read_yaml_file_as_json(self, path):
        def_yaml = self._read_file_content(path)
        return yaml.safe_load(def_yaml)

    def test_missing_version(self):
        def_dict = self._read_yaml_file_as_json(WB_PRE_XFORM_PATH)
        del def_dict['version']
        def_yaml = yaml.safe_dump(def_dict)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("'version' is a required property", cm.exception.message)

    def test_unsupported_version(self):
        def_dict = self._read_yaml_file_as_json(WB_PRE_XFORM_PATH)
        def_dict['version'] = '1.0'
        def_yaml = yaml.safe_dump(def_dict)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn('Unsupported DSL version', cm.exception.message)

    def test_required_action_params_failure(self):
        def_yaml = self._read_file_content(WF_NO_REQ_PARAM_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn('Missing required parameters', cm.exception.message)

    def test_unexpected_action_params_failure(self):
        def_yaml = self._read_file_content(WF_UNEXP_PARAM_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn('Unexpected parameters', cm.exception.message)

    def test_deprecated_callback_action(self):
        def_dict = self._read_yaml_file_as_json(WB_PRE_XFORM_PATH)
        def_dict['workflows']['main']['tasks']['callback'] = {'action': 'st2.callback'}
        def_yaml = yaml.safe_dump(def_dict)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn('st2.callback is deprecated', cm.exception.message)

    @mock.patch.object(
        workbooks.WorkbookManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': True}
            ]
        )
    )
    def test_workbook_valid(self):
        def_yaml = self._read_file_content(WB_PRE_XFORM_PATH)
        self.validator.validate(def_yaml)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': False, 'error': 'Invalid DSL: foobar\n\nFailed to validate...'},
                {'valid': True}
            ]
        )
    )
    def test_workbook_invalid_syntax(self):
        def_yaml = self._read_file_content(WB_INVALID_SYNTAX_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("DSL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': False, 'error': 'Invalid DSL: foobar\n\nFailed to validate...'}
            ]
        )
    )
    def test_workbook_invalid_syntax_post_transformed(self):
        def_yaml = self._read_file_content(WB_INVALID_SYNTAX_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("DSL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': False, 'error': 'Parse error: unexpected end of statement.'},
                {'valid': True}
            ]
        )
    )
    def test_workbook_invalid_yaql(self):
        def_yaml = self._read_file_content(WB_INVALID_YAQL_PATH)

        with self.assertRaises(Exception) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("YAQL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': False, 'error': 'Parse error: unexpected end of statement.'}
            ]
        )
    )
    def test_workbook_invalid_yaql_post_transformed(self):
        def_yaml = self._read_file_content(WB_INVALID_YAQL_PATH)

        with self.assertRaises(Exception) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("YAQL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': True}
            ]
        )
    )
    def test_workflow_valid(self):
        def_yaml = self._read_file_content(WF_PRE_XFORM_PATH)
        self.validator.validate(def_yaml)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': False, 'error': 'Invalid DSL: foobar\n\nFailed to validate...'},
                {'valid': True}
            ]
        )
    )
    def test_workflow_invalid_syntax(self):
        def_yaml = self._read_file_content(WF_INVALID_SYNTAX_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("DSL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': False, 'error': 'Invalid DSL: foobar\n\nFailed to validate...'}
            ]
        )
    )
    def test_workflow_invalid_syntax_post_transformed(self):
        def_yaml = self._read_file_content(WF_INVALID_SYNTAX_PATH)

        with self.assertRaises(WorkflowDefinitionException) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("DSL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': False, 'error': 'Parse error: unexpected end of statement.'},
                {'valid': True}
            ]
        )
    )
    def test_workflow_invalid_yaql(self):
        def_yaml = self._read_file_content(WF_INVALID_YAQL_PATH)

        with self.assertRaises(Exception) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("YAQL ERROR", cm.exception.message)

    @mock.patch.object(
        workflows.WorkflowManager, 'validate',
        mock.MagicMock(
            side_effect=[
                {'valid': True},
                {'valid': False, 'error': 'Parse error: unexpected end of statement.'}
            ]
        )
    )
    def test_workflow_invalid_yaql_post_transformed(self):
        def_yaml = self._read_file_content(WF_INVALID_YAQL_PATH)

        with self.assertRaises(Exception) as cm:
            self.validator.validate(def_yaml)

        self.assertIn("YAQL ERROR", cm.exception.message)
