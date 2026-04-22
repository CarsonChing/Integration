import unittest
from unittest.mock import patch

import demo
from security import EthicalGuard, InputValidator, RateLimiter


class TestInputValidator(unittest.TestCase):
    def setUp(self):
        self.v = InputValidator(max_length=10)

    def test_accepts_within_limit(self):
        ok, msg = self.v.validate("hello")
        self.assertTrue(ok)
        self.assertEqual(msg, "hello")

    def test_sanitizes_and_returns_clean_text(self):
        ok, msg = self.v.validate("  hi \x00 there  ")
        self.assertTrue(ok)
        self.assertEqual(msg, "hi there")

    def test_strips_control_chars(self):
        ok, msg = self.v.validate("a\x01\x02b")
        self.assertTrue(ok)
        self.assertEqual(msg, "ab")

    def test_rejects_non_string(self):
        ok, msg = self.v.validate(None)
        self.assertFalse(ok)
        self.assertIn("string", msg)

    def test_rejects_empty_after_strip(self):
        ok, msg = self.v.validate("   \n\t  ")
        self.assertFalse(ok)
        self.assertIn("empty", msg.lower())

    def test_rejects_over_max_length(self):
        ok, msg = self.v.validate("x" * 11)
        self.assertFalse(ok)
        self.assertIn("10", msg)

    def test_sanitize_strips_tags(self):
        self.assertEqual(self.v.sanitize("<b>x</b>"), "x")


class TestRateLimiter(unittest.TestCase):
    def test_allows_exactly_max_requests(self):
        rl = RateLimiter(max_requests=10, window_seconds=60)
        with patch("security.time.time", return_value=50.0):
            for _ in range(10):
                ok, _ = rl.check("session-a")
                self.assertTrue(ok)

    def test_blocks_eleventh_in_same_window(self):
        rl = RateLimiter(max_requests=10, window_seconds=60)
        with patch("security.time.time", return_value=0.0):
            for _ in range(10):
                self.assertTrue(rl.check("s")[0])
            ok, msg = rl.check("s")
            self.assertFalse(ok)
            self.assertIn("Rate limit", msg)

    def test_resets_after_window(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        with patch("security.time.time", side_effect=[0.0, 0.0, 0.0, 0.0]):
            self.assertTrue(rl.check("w")[0])
            self.assertTrue(rl.check("w")[0])
            self.assertTrue(rl.check("w")[0])
            self.assertFalse(rl.check("w")[0])
        rl2 = RateLimiter(max_requests=3, window_seconds=60)
        with patch("security.time.time", side_effect=[0.0, 0.0, 0.0, 100.0]):
            self.assertTrue(rl2.check("w")[0])
            self.assertTrue(rl2.check("w")[0])
            self.assertTrue(rl2.check("w")[0])
            self.assertTrue(rl2.check("w")[0])


class TestEthicalGuard(unittest.TestCase):
    def test_clean_text_ok(self):
        g = EthicalGuard(patterns=["__BAD__"])
        self.assertEqual(g.screen("all good here"), (True, "OK"))

    def test_flagged_returns_message(self):
        g = EthicalGuard(patterns=["__BAD__"])
        ok, msg = g.screen("contains __BAD__ token")
        self.assertFalse(ok)
        self.assertIn("policy", msg.lower())

    def test_logs_warning_when_flagged(self):
        g = EthicalGuard(patterns=["__BAD__"])
        with self.assertLogs("security", level="WARNING") as cm:
            g.screen("prefix __BAD__ suffix", context="unit_test")
        self.assertTrue(any("EthicalGuard" in r or "__BAD__" in r for r in cm.output))


class TestDemoWorkflow(unittest.TestCase):
    def test_happy_path(self):
        with patch.object(demo, "deepseek_model", side_effect=demo.stub_model):
            r = demo.run_secured_agent_turn("t-session", "hello")
        self.assertTrue(r["ok"])
        self.assertIn("response", r)

    def test_validation_failure_stage(self):
        with patch.object(demo, "deepseek_model", side_effect=demo.stub_model):
            r = demo.run_secured_agent_turn("t2", "")
        self.assertFalse(r["ok"])
        self.assertEqual(r["stage"], "validation")


if __name__ == "__main__":
    unittest.main()
