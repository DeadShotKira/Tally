"""Unit tests for the PrivacyEngine."""

import unittest
from backend.app.features.imports.privacy import PrivacyEngine


class TestPrivacyEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PrivacyEngine()

    def test_sanitize_empty_and_whitespace(self) -> None:
        result = self.engine.sanitize_description("")
        self.assertEqual(result.sanitized_description, "")
        self.assertEqual(result.redactions, ())

        result = self.engine.sanitize_description("   ")
        self.assertEqual(result.sanitized_description, "")
        self.assertEqual(result.redactions, ())

    def test_sanitize_safe_text(self) -> None:
        text = "Starbucks Coffee Mumbai"
        result = self.engine.sanitize_description(text)
        self.assertEqual(result.sanitized_description, text)
        self.assertEqual(result.redactions, ())

    def test_sanitize_account_number_formats(self) -> None:
        formats = [
            "payment to a/c 123456789012",
            "payment to acct: 98765432101234",
            "acc no. 12345678",
            "account no - 99999999999",
        ]
        for text in formats:
            result = self.engine.sanitize_description(text)
            self.assertIn("[ACCOUNT_REDACTED]", result.sanitized_description)
            self.assertNotIn("12345678", result.sanitized_description)
            self.assertIn("ACCOUNT", result.redactions)

    def test_sanitize_upi_id(self) -> None:
        text = "UPI transaction to rahul.kumar@okhdfcbank"
        result = self.engine.sanitize_description(text)
        self.assertIn("[UPI_REDACTED]", result.sanitized_description)
        self.assertNotIn("rahul.kumar@okhdfcbank", result.sanitized_description)
        self.assertIn("UPI", result.redactions)

    def test_sanitize_phone_number(self) -> None:
        text = "ordered from swiggy support +91 9876543210"
        result = self.engine.sanitize_description(text)
        self.assertIn("[PHONE_REDACTED]", result.sanitized_description)
        self.assertNotIn("9876543210", result.sanitized_description)
        self.assertIn("PHONE", result.redactions)

    def test_sanitize_ifsc(self) -> None:
        text = "IFSC code ICIC0000104 bank transfer"
        result = self.engine.sanitize_description(text)
        self.assertIn("[IFSC_REDACTED]", result.sanitized_description)
        self.assertNotIn("ICIC0000104", result.sanitized_description)
        self.assertIn("IFSC", result.redactions)

    def test_sanitize_customer_id(self) -> None:
        text = "cust id: 123456789 customer id 998877"
        result = self.engine.sanitize_description(text)
        self.assertIn("[CUSTOMER_ID_REDACTED]", result.sanitized_description)
        self.assertIn("CUSTOMER_ID", result.redactions)

    def test_sanitize_long_number(self) -> None:
        text = "reference txn sequence number 123456789012345"
        result = self.engine.sanitize_description(text)
        self.assertIn("[LONG_NUMBER_REDACTED]", result.sanitized_description)
        self.assertNotIn("123456789012345", result.sanitized_description)
        self.assertIn("LONG_NUMBER", result.redactions)

    def test_sanitize_email_and_card_number(self) -> None:
        result = self.engine.sanitize_description(
            "receipt jane.doe@example.com card 4111 1111 1111 1111"
        )
        self.assertIn("[EMAIL_REDACTED]", result.sanitized_description)
        self.assertIn("[CARD_REDACTED]", result.sanitized_description)
        self.assertNotIn("jane.doe@example.com", result.sanitized_description)
        self.assertNotIn("4111 1111 1111 1111", result.sanitized_description)

    def test_assert_safe_for_storage_success(self) -> None:
        # Safe string should not raise
        self.engine.assert_safe_for_storage("Starbucks Coffee")

    def test_assert_safe_for_storage_failure(self) -> None:
        # Unsafe string should raise ValueError and NOT leak raw values
        with self.assertRaises(ValueError) as ctx:
            self.engine.assert_safe_for_storage("a/c 123456789012")
        self.assertIn("Storage safety check failed", str(ctx.exception))
        self.assertNotIn("123456789012", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
