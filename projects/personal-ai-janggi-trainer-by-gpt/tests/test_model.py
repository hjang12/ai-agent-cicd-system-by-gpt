import unittest

from janggi import ModelRegistry, ModelSpec


class ModelRegistryTests(unittest.TestCase):
    def test_model_spec_validates_identity(self):
        with self.assertRaises(ValueError):
            ModelSpec("", "Model", "engine")
        with self.assertRaises(ValueError):
            ModelSpec("model", "", "engine")
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "")

    def test_model_spec_rejects_non_string_identity(self):
        with self.assertRaises(ValueError):
            ModelSpec(123, "Model", "engine")
        with self.assertRaises(ValueError):
            ModelSpec("model", 123, "engine")
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", 123)

    def test_model_spec_validates_optional_metadata_types(self):
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "engine", engine_version=1)
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "engine", source=1)

    def test_model_spec_validates_rating(self):
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "engine", rating=-1)
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "engine", rating=True)
        with self.assertRaises(ValueError):
            ModelSpec("model", "Model", "engine", rating="1000")

    def test_registry_register_get_and_list(self):
        first = ModelSpec(
            "negamax-d2",
            "Negamax Depth 2",
            "negamax",
            engine_version="1",
            rating=1000,
            source="builtin",
        )
        second = ModelSpec("negamax-d3", "Negamax Depth 3", "negamax", rating=1100)
        registry = ModelRegistry([first])

        registry.register(second)

        self.assertEqual(registry.get("negamax-d2"), first)
        self.assertEqual(registry.maybe_get("missing"), None)
        self.assertEqual(registry.list(), (first, second))
        self.assertEqual(len(registry), 2)
        self.assertIn("negamax-d3", registry)

    def test_registry_rejects_duplicate_ids(self):
        model = ModelSpec("model", "Model", "engine")
        registry = ModelRegistry([model])

        with self.assertRaises(ValueError):
            registry.register(model)

    def test_registry_rejects_non_model_spec(self):
        registry = ModelRegistry()

        with self.assertRaises(ValueError):
            registry.register("model")

    def test_registry_get_rejects_unknown_id(self):
        registry = ModelRegistry()

        with self.assertRaises(KeyError):
            registry.get("missing")


if __name__ == "__main__":
    unittest.main()
