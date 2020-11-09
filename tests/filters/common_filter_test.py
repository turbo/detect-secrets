import re

import pytest

from detect_secrets import main as main_module
from detect_secrets.constants import VerifiedResult
from detect_secrets.plugins.base import RegexBasedDetector
from testing.mocks import mock_printer
from testing.plugins import register_plugin


class TestVerify:
    @staticmethod
    def test_does_not_verify_if_no_verify():
        with register_plugin(MockPlugin(should_verify=False)):
            main_module.main(['scan', '--string', 'fake-secret', '--no-verify'])

    @staticmethod
    @pytest.mark.parametrize(
        'args, verified_result, should_be_present',
        (
            ([], VerifiedResult.UNVERIFIED, True),
            ([], VerifiedResult.VERIFIED_TRUE, True),
            (['--only-verified'], VerifiedResult.UNVERIFIED, False),
            (['--only-verified'], VerifiedResult.VERIFIED_TRUE, True),
        ),
    )
    def test_adheres_to_verification_policies(args, verified_result, should_be_present):
        with register_plugin(
            MockPlugin(verified_result=verified_result),
        ), mock_printer(main_module) as printer:
            main_module.main(['scan', '--string', 'fake-secret', *args])

        for line in printer.message.splitlines():
            plugin_name, result = [x.strip() for x in line.split(':')]
            if plugin_name != 'MockPlugin':
                continue

            assert should_be_present == (result == 'True')

    @staticmethod
    def test_supports_injection_of_context():
        with register_plugin(ContextAwareMockPlugin()):
            main_module.main(['scan', '--string', 'fake-secret'])


class MockPlugin(RegexBasedDetector):
    denylist = (
        re.compile('fake-secret'),
    )
    secret_type = 'mock plugin'

    def __init__(self, should_verify=True, verified_result=VerifiedResult.UNVERIFIED):
        self.should_verify = should_verify
        self.verified_result = verified_result

    # TODO: Need to inject context.
    def verify(self, secret):
        if not self.should_verify:
            raise AssertionError('Verification should not occur.')

        return self.verified_result


class ContextAwareMockPlugin(MockPlugin):
    def verify(self, secret, context):
        return VerifiedResult.UNVERIFIED