import unittest

from bjt import (
    BiasInputs,
    relative_difference,
    solve_linear_system,
    solve_nodal,
    solve_thevenin,
    thevenin_equivalent,
    validate,
)

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


class TestThevenin(unittest.TestCase):
    def test_equivalent(self):
        vbb, rb = thevenin_equivalent(BiasInputs(**VALID))
        self.assertAlmostEqual(vbb, 2.1052632, delta=1e-6)
        self.assertAlmostEqual(rb, 8245.614, delta=1e-2)

    def test_reference_qpoint(self):
        r = solve_thevenin(BiasInputs(**VALID))
        self.assertAlmostEqual(r["ib"], 8.8245e-6, delta=1e-9)
        self.assertAlmostEqual(r["ic"], 1.323675e-3, delta=1e-8)
        self.assertAlmostEqual(r["ie"], 1.33249e-3, delta=1e-8)
        self.assertAlmostEqual(r["vb"], 2.0325, delta=1e-4)
        self.assertAlmostEqual(r["ve"], 1.33249, delta=1e-4)
        self.assertAlmostEqual(r["vc"], 9.087915, delta=1e-4)
        self.assertAlmostEqual(r["vce"], 7.755425, delta=1e-4)

    def test_kirchhoff_holds(self):
        r = solve_thevenin(BiasInputs(**VALID))
        self.assertAlmostEqual(r["ib"] + r["ic"], r["ie"], delta=1e-12)


class TestNodal(unittest.TestCase):
    def test_gaussian_elimination(self):
        x = solve_linear_system([[2.0, 1.0], [1.0, -1.0]], [5.0, 1.0])
        self.assertAlmostEqual(x[0], 2.0)
        self.assertAlmostEqual(x[1], 1.0)

    def test_singular_system_raises(self):
        with self.assertRaises(ValueError):
            solve_linear_system([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

    def test_agrees_with_thevenin_on_fixtures(self):
        fixtures = (
            VALID,
            {**VALID, "rc": 47000.0},
            {**VALID, "r1": 70000.0, "re": 100.0},
            {**VALID, "r1": 1000.0, "r2": 10000.0, "rc": 10.0, "re": 10.0, "beta": 10.0},
        )
        for fixture in fixtures:
            with self.subTest(fixture=fixture):
                inputs = BiasInputs(**fixture)
                diff = relative_difference(solve_thevenin(inputs), solve_nodal(inputs))
                self.assertLess(diff, 1e-9)


if __name__ == "__main__":
    unittest.main()
