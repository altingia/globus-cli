import unittest
try:
    import M2Crypto
    # slightly hacky way of preventing flake8 from complaining
    m2crypto_imported = bool(M2Crypto)
except ImportError:
    m2crypto_imported = False

from globus_cli.helpers import fill_delegate_proxy_activation_requirements
from tests.framework.cli_testcase import CliTestCase
from tests.framework.constants import GO_EP1_ID, PUBLIC_KEY


class DelegateProxyTests(CliTestCase):

    @unittest.skipIf(m2crypto_imported, "M2Crypto successfully imported")
    def test_m2crypto_not_imported(self):
        """
        Confirms --delegate-proxy doesn't appear in activate help text
        if M2Crypto is not available. Confirms error if option is attempted
        to be used anyways.
        """
        output = self.run_line("globus endpoint activate --help")
        self.assertNotIn("--delegate-proxy", output)

        output = self.run_line((
            "globus endpoint activate {} --delegate-proxy cert.pem"
            .format(GO_EP1_ID)), assert_exit_code=1)
        self.assertIn("Missing M2Crypto dependency", output)

    @unittest.skipIf(not m2crypto_imported, "M2Crypto not imported")
    def test_m2crypto_imported(self):
        """
        Confirms --delegate-proxy does appear in activate help text if
        M2Crypto was successfully imported.
        Confirms the tutorial endpoints cannot use delegate_proxy activation.
        """
        output = self.run_line("globus endpoint activate --help")
        self.assertIn("--delegate-proxy", output)

        # --force and --no-autoactivate are used to prevent the endpoint being
        # seen as not needing activation
        output = self.run_line((
            "globus endpoint activate {} --delegate-proxy cert.pem "
            "--no-autoactivate --force".format(GO_EP1_ID)), assert_exit_code=1)
        self.assertIn(
            "this endpoint does not support Delegate Proxy activation", output)

    @unittest.skipIf(not m2crypto_imported, "M2Crypto not imported")
    def test_fill_delegate_proxy_activation_requirements(self):
        """
        Uses the public key from constants to form a fake activation
        requirements response, and an expired proxy to test
        fill_delegate_proxy_activation_requirements.
        """
        # file containing an expired x509 from a myproxy-logon
        x509 = "tests/framework/files/cert.pem"

        activation_requirements = {
            "DATA_TYPE": "activation_requirements",
            "DATA": [
                {"DATA_TYPE": "activation_requirement",
                 "type": "delegate_proxy",
                 "name": "public_key",
                 "value": PUBLIC_KEY},
                {"DATA_TYPE": "activation_requirement",
                 "type": "delegate_proxy",
                 "name": "proxy_chain",
                 "value": None}]}

        filled_requirements = fill_delegate_proxy_activation_requirements(
            activation_requirements, x509)

        # assert the proxy_chain now contains a certificate
        self.assertIn("-----BEGIN CERTIFICATE-----",
                      filled_requirements["DATA"][1]["value"])
        self.assertIn("-----END CERTIFICATE-----",
                      filled_requirements["DATA"][1]["value"])

    @unittest.skipIf(not m2crypto_imported, "M2Crypto not imported")
    def test_bad_x509(self):
        """
        Uses the public key from constants to form a fake activation
        requirements response, then attempts to fill the activation
        requirements with bad x509 files. Confirms value errors
        """
        activation_requirements = {
            "DATA_TYPE": "activation_requirements",
            "DATA": [
                {"DATA_TYPE": "activation_requirement",
                 "type": "delegate_proxy",
                 "name": "public_key",
                 "value": PUBLIC_KEY},
                {"DATA_TYPE": "activation_requirement",
                 "type": "delegate_proxy",
                 "name": "proxy_chain",
                 "value": None}]}

        # no file
        with self.assertRaises(IOError) as err:
            fill_delegate_proxy_activation_requirements(
                activation_requirements, "nosuchfile.pem")
        self.assertIn("No such file", str(err.exception))

        # non pem file
        with self.assertRaises(ValueError) as err:
            fill_delegate_proxy_activation_requirements(
                activation_requirements, "tests/framework/constants.py")
        self.assertIn("Unable to find private key", str(err.exception))

        # no private key
        with self.assertRaises(ValueError) as err:
            fill_delegate_proxy_activation_requirements(
                activation_requirements, "tests/framework/files/no_key.pem")
        self.assertIn("Unable to find private key", str(err.exception))

        # no certificate
        with self.assertRaises(ValueError) as err:
            fill_delegate_proxy_activation_requirements(
                activation_requirements, "tests/framework/files/no_cert.pem")
        self.assertIn("Error parsing credentials", str(err.exception))
