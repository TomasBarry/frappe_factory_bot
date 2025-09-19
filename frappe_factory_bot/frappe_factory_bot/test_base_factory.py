import unittest
from typing import Any
from unittest.mock import MagicMock, patch

from frappe.model.document import Document

from frappe_factory_bot.frappe_factory_bot.base_factory import BaseFactory


class TestDocType(Document):  # type: ignore
    """Mock document type for testing"""

    pass


class MockFactory(BaseFactory):
    """Test factory for testing BaseFactory functionality"""

    doctype = "Test DocType"

    @property
    def default_attributes(self) -> dict[str, Any]:
        return {
            "name": "Test Document",
            "field1": "default_value1",
            "field2": 100,
            "is_active": 1,
        }

    @property
    def with_custom_name(self) -> dict[str, Any]:
        return {"name": "Custom Name Document"}

    @property
    def with_special_fields(self) -> dict[str, Any]:
        return {"field1": "special_value", "field3": "special_field3"}

    @property
    def with_numbers(self) -> dict[str, Any]:
        return {"field2": 999, "field4": 42}


class MockFactoryNoDefaults(BaseFactory):
    """Test factory with no default attributes"""

    doctype = "Empty DocType"

    @property
    def default_attributes(self) -> dict[str, Any]:
        return {}

    @property
    def with_basic_fields(self) -> dict[str, Any]:
        return {"name": "Basic Document", "field1": "basic_value"}


class TestBaseFactory(unittest.TestCase):
    """Comprehensive tests for BaseFactory class"""

    def setUp(self) -> None:
        """Set up test environment"""
        self.mock_doc = self._create_mock_document()

    def _create_mock_document(self, name: str = "test-document-001") -> MagicMock:
        """Create a properly configured mock document with common properties"""
        mock_doc = MagicMock(spec=TestDocType)
        mock_doc.name = name
        mock_doc.insert = MagicMock()
        mock_doc.flags = {}
        return mock_doc

    def _create_mock_documents(
        self, count: int, name_prefix: str = "test-document"
    ) -> list[MagicMock]:
        """Create multiple properly configured mock documents with unique names"""
        return [
            self._create_mock_document(f"{name_prefix}-{i:03d}")
            for i in range(1, count + 1)
        ]

    @patch("frappe.get_doc")
    def test_build_creates_unsaved_document(self, mock_get_doc: MagicMock) -> None:
        """Test that build() creates an unsaved document with default attributes"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build()

        mock_get_doc.assert_called_once_with(
            {
                "name": "Test Document",
                "field1": "default_value1",
                "field2": 100,
                "is_active": 1,
                "doctype": "Test DocType",
            }
        )
        self.mock_doc.insert.assert_not_called()
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_build_with_traits(self, mock_get_doc: MagicMock) -> None:
        """Test that build() applies traits correctly"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build("with_custom_name", "with_special_fields")

        mock_get_doc.assert_called_once_with(
            {
                "name": "Custom Name Document",  # from with_custom_name trait
                "field1": "special_value",  # from with_special_fields trait
                "field2": 100,  # from default_attributes
                "field3": "special_field3",  # from with_special_fields trait
                "is_active": 1,  # from default_attributes
                "doctype": "Test DocType",
            }
        )
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_build_with_overrides(self, mock_get_doc: MagicMock) -> None:
        """Test that build() applies overrides correctly"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build(
            name="Override Name", field1="override_value", new_field="new_value"
        )

        mock_get_doc.assert_called_once_with(
            {
                "name": "Override Name",  # overridden
                "field1": "override_value",  # overridden
                "field2": 100,  # from default_attributes
                "is_active": 1,  # from default_attributes
                "new_field": "new_value",  # new field from override
                "doctype": "Test DocType",
            }
        )
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_build_with_flags(self, mock_get_doc: MagicMock) -> None:
        """Test that build() applies flags correctly"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build(flags={"flag1": "value_1", "flag2": "value_2"})

        # `flags` should not propagate into `get_doc`
        mock_get_doc.assert_called_once_with(
            {
                "name": "Test Document",  # from default_attributes
                "field1": "default_value1",  # from default_attributes
                "field2": 100,  # from default_attributes
                "is_active": 1,  # from default_attributes
                "doctype": "Test DocType",
            }
        )
        self.assertEqual(result, self.mock_doc)
        self.assertEqual(result.flags["flag1"], "value_1")
        self.assertEqual(result.flags["flag2"], "value_2")

    @patch("frappe.get_doc")
    def test_build_precedence_order(self, mock_get_doc: MagicMock) -> None:
        """Test that overrides take precedence over traits, which take precedence over defaults"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build(
            "with_custom_name", "with_numbers", name="Final Override", field2=777
        )

        mock_get_doc.assert_called_once_with(
            {
                "name": "Final Override",  # override wins over trait
                "field1": "default_value1",  # from default_attributes (no trait or override)
                "field2": 777,  # override wins over trait
                "field4": 42,  # from with_numbers trait
                "is_active": 1,  # from default_attributes
                "doctype": "Test DocType",
            }
        )
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_create_saves_document(self, mock_get_doc: MagicMock) -> None:
        """Test that create() saves the document"""
        mock_get_doc.return_value = self.mock_doc

        with patch.object(MockFactory, "_attach_del") as mock_attach_del:
            result = MockFactory.create()

        mock_get_doc.assert_called_once_with(
            {
                "name": "Test Document",
                "field1": "default_value1",
                "field2": 100,
                "is_active": 1,
                "doctype": "Test DocType",
            }
        )
        self.mock_doc.insert.assert_called_once()
        mock_attach_del.assert_called_once_with(self.mock_doc)
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_create_with_traits_and_overrides(self, mock_get_doc: MagicMock) -> None:
        """Test that create() works with traits and overrides"""
        mock_get_doc.return_value = self.mock_doc

        with patch.object(MockFactory, "_attach_del") as mock_attach_del:
            result = MockFactory.create("with_special_fields", field1="create_override")

        mock_get_doc.assert_called_once_with(
            {
                "name": "Test Document",  # from default_attributes
                "field1": "create_override",  # override wins over trait
                "field2": 100,  # from default_attributes
                "field3": "special_field3",  # from with_special_fields trait
                "is_active": 1,  # from default_attributes
                "doctype": "Test DocType",
            }
        )
        self.mock_doc.insert.assert_called_once()
        mock_attach_del.assert_called_once_with(self.mock_doc)
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_build_list(self, mock_get_doc: MagicMock) -> None:
        """Test that build_list() creates multiple unsaved documents"""
        mock_docs = self._create_mock_documents(3)
        mock_get_doc.side_effect = mock_docs

        result = MockFactory.build_list(3)

        self.assertEqual(len(result), 3)
        self.assertEqual(mock_get_doc.call_count, 3)
        for _, mock_doc in enumerate(mock_docs):
            mock_doc.insert.assert_not_called()
        self.assertEqual(result, mock_docs)

    @patch("frappe.get_doc")
    def test_build_list_with_traits_and_overrides(
        self, mock_get_doc: MagicMock
    ) -> None:
        """Test that build_list() applies traits and overrides to all documents"""
        mock_docs = self._create_mock_documents(2)
        mock_get_doc.side_effect = mock_docs

        result = MockFactory.build_list(2, "with_custom_name", field1="list_override")

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_get_doc.call_count, 2)

        expected_call_args = {
            "name": "Custom Name Document",
            "field1": "list_override",
            "field2": 100,
            "is_active": 1,
            "doctype": "Test DocType",
        }

        for call in mock_get_doc.call_args_list:
            self.assertEqual(call[0][0], expected_call_args)

    @patch("frappe.get_doc")
    def test_create_list(self, mock_get_doc: MagicMock) -> None:
        """Test that create_list() creates and saves multiple documents"""
        mock_docs = self._create_mock_documents(3)
        mock_get_doc.side_effect = mock_docs

        with patch.object(MockFactory, "_attach_del") as mock_attach_del:
            result = MockFactory.create_list(3)

        self.assertEqual(len(result), 3)
        self.assertEqual(mock_get_doc.call_count, 3)
        self.assertEqual(mock_attach_del.call_count, 3)

        for mock_doc in mock_docs:
            mock_doc.insert.assert_called_once()

        self.assertEqual(result, mock_docs)

    @patch("frappe.get_doc")
    def test_create_list_with_traits_and_overrides(
        self, mock_get_doc: MagicMock
    ) -> None:
        """Test that create_list() applies traits and overrides to all documents"""
        mock_docs = self._create_mock_documents(2)
        mock_get_doc.side_effect = mock_docs

        with patch.object(MockFactory, "_attach_del") as mock_attach_del:
            result = MockFactory.create_list(2, "with_numbers", field2=555)

        self.assertEqual(len(result), 2)
        self.assertEqual(mock_get_doc.call_count, 2)
        self.assertEqual(mock_attach_del.call_count, 2)

        expected_call_args = {
            "name": "Test Document",
            "field1": "default_value1",
            "field2": 555,  # override wins over trait
            "field4": 42,  # from with_numbers trait
            "is_active": 1,
            "doctype": "Test DocType",
        }

        for call in mock_get_doc.call_args_list:
            self.assertEqual(call[0][0], expected_call_args)

    def test_invalid_traits_raises_error(self) -> None:
        """Test that using invalid traits raises TypeError"""
        with self.assertRaises(TypeError) as context:
            MockFactory("invalid_trait", "with_custom_name")

        self.assertIn(
            "must be a subset of the set of valid traits", str(context.exception)
        )
        self.assertIn("invalid_trait", str(context.exception))

    def test_valid_traits_detection(self) -> None:
        """Test that valid traits are correctly detected"""
        # This should not raise an error
        try:
            _ = MockFactory("with_custom_name", "with_special_fields", "with_numbers")
            valid_traits = [
                name
                for name, value in MockFactory.__dict__.items()
                if isinstance(value, property) and name != "default_attributes"
            ]
            expected_traits = {
                "with_custom_name",
                "with_special_fields",
                "with_numbers",
            }
            self.assertTrue(expected_traits.issubset(set(valid_traits)))
        except TypeError:
            self.fail("Valid traits should not raise TypeError")

    @patch("frappe.get_doc")
    def test_empty_default_attributes(self, mock_get_doc: MagicMock) -> None:
        """Test factory with empty default attributes"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactoryNoDefaults.build("with_basic_fields")

        mock_get_doc.assert_called_once_with(
            {
                "name": "Basic Document",
                "field1": "basic_value",
                "doctype": "Empty DocType",
            }
        )
        self.assertEqual(result, self.mock_doc)

    @patch("frappe.get_doc")
    def test_doctype_cannot_be_overridden(self, mock_get_doc: MagicMock) -> None:
        """Test that doctype cannot be overridden in factory calls"""
        mock_get_doc.return_value = self.mock_doc

        result = MockFactory.build(doctype="Malicious DocType")

        # Should still use the factory's doctype, not the override
        mock_get_doc.assert_called_once_with(
            {
                "name": "Test Document",
                "field1": "default_value1",
                "field2": 100,
                "is_active": 1,
                "doctype": "Test DocType",  # Factory doctype takes precedence
            }
        )
        self.assertEqual(result, self.mock_doc)

    def test_attach_del_creates_temp_subclass(self) -> None:
        """Test that _attach_del creates a temporary subclass with custom __del__"""
        mock_obj = MagicMock()
        original_class = mock_obj.__class__

        MockFactory._attach_del(mock_obj)

        # Object should now have a different class
        self.assertNotEqual(mock_obj.__class__, original_class)
        self.assertTrue(issubclass(mock_obj.__class__, original_class))
        self.assertEqual(mock_obj.__class__.__name__, "TempSubclass")

        # Should have the custom __del__ method
        self.assertTrue(hasattr(mock_obj.__class__, "__del__"))

    def test_del_override_is_callable(self) -> None:
        """Test that __del_override__ method is callable and doesn't raise errors"""
        # This should not raise any errors
        try:
            MockFactory.__del_override__(MagicMock())
        except Exception as e:
            self.fail(f"__del_override__ should not raise an exception: {e}")

    @patch("frappe.get_doc")
    def test_factory_traits_attribute_is_set(self, mock_get_doc: MagicMock) -> None:
        """Test that factory_traits attribute is properly set"""
        mock_get_doc.return_value = self.mock_doc

        factory = MockFactory("with_custom_name", "with_special_fields")

        self.assertEqual(
            factory.factory_traits, ["with_custom_name", "with_special_fields"]
        )
        self.assertIsInstance(factory.factory_traits, list)

    @patch("frappe.get_doc")
    def test_overrides_attribute_is_set(self, mock_get_doc: MagicMock) -> None:
        """Test that overrides attribute is properly set during build/create"""
        mock_get_doc.return_value = self.mock_doc

        # Create a factory instance to test that overrides are set
        instance = MockFactory("with_custom_name")
        instance.overrides = {"field1": "test_override", "field2": 999}

        # Test that the overrides attribute exists and contains expected values
        self.assertIsInstance(instance.overrides, dict)
        self.assertEqual(instance.overrides["field1"], "test_override")
        self.assertEqual(instance.overrides["field2"], 999)

    def test_attributes_property_combines_defaults_and_traits(self) -> None:
        """Test that attributes property correctly combines default_attributes and traits"""
        factory = MockFactory("with_special_fields", "with_numbers")

        expected_attributes = {
            "name": "Test Document",  # from default_attributes
            "field1": "special_value",  # overridden by with_special_fields
            "field2": 999,  # overridden by with_numbers
            "field3": "special_field3",  # from with_special_fields
            "field4": 42,  # from with_numbers
            "is_active": 1,  # from default_attributes
        }

        self.assertEqual(factory.attributes, expected_attributes)

    def test_attributes_property_with_no_traits(self) -> None:
        """Test that attributes property returns default_attributes when no traits are used"""
        factory = MockFactory()

        expected_attributes = {
            "name": "Test Document",
            "field1": "default_value1",
            "field2": 100,
            "is_active": 1,
        }

        self.assertEqual(factory.attributes, expected_attributes)


if __name__ == "__main__":
    unittest.main()
