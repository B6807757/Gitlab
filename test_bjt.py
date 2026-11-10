import unittest

from bjt import BiasInputs, validate

VALID = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=2200.0, re=1000.0, beta=150.0, vbe=0.7)


class TestValidation(unittest.TestCase):
    def test_accepts_reference_values(self):
        validate(BiasInputs(**VALID))

    def test_accepts_beta_of_one(self):
        validate(BiasInputs(**{**VALID, "beta": 1.0}))

    def test_rejects_non_positive_supply_and_resistors(self):
        for field in ("vcc", "r1", "r2", "rc", "re"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, field: 0.0}))
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, field: -1.0}))

    def test_error_names_the_field(self):
        with self.assertRaises(ValueError) as ctx:
            validate(BiasInputs(**{**VALID, "r1": 0.0}))
        self.assertIn("R1", str(ctx.exception))

    def test_rejects_beta_below_one(self):
        for beta in (0.0, 0.5):
            with self.subTest(beta=beta):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "beta": beta}))

    def test_rejects_vbe_outside_range(self):
        for vbe in (-0.1, 12.0, 13.0):
            with self.subTest(vbe=vbe):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "vbe": vbe}))

    def test_rejects_non_finite_values(self):
        for value in (float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate(BiasInputs(**{**VALID, "r2": value}))


if __name__ == "__main__":
    unittest.main()
