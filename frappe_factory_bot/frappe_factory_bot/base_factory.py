from functools import reduce
from typing import Any

import frappe
from frappe.model.document import Document


class BaseFactory:
    factory_traits: list[str]
    doctype: str
    overrides: dict[str, Any]

    @classmethod
    def build(cls, *_factory_traits: str, **overrides: Any) -> Document:
        instance = cls(*_factory_traits)
        instance.overrides = overrides
        # Assign doctype last so that it cannot be overridden
        doctype = frappe.get_doc(
            {**instance.attributes, **overrides, "doctype": instance.doctype}
        )
        doctype.flags.update(**overrides.get("flags", {}))

        return doctype

    @classmethod
    def build_list(
        cls, n: int, *_factory_traits: str, **overrides: Any
    ) -> list[Document]:
        return [cls.build(*_factory_traits, **overrides) for _ in range(n)]

    @classmethod
    def create(cls, *_factory_traits: str, **overrides: Any) -> Document:
        doctype = cls.build(*_factory_traits, **overrides)
        doctype.insert()
        cls._attach_del(doctype)

        return doctype

    @classmethod
    def create_list(
        cls, n: int, *_factory_traits: str, **overrides: Any
    ) -> list[Document]:
        return [cls.create(*_factory_traits, **overrides) for _ in range(n)]

    def __init__(self, *factory_traits: str) -> None:
        self.factory_traits = list(factory_traits)

        # Making sure that we don't use a trait that does not exist - it would be
        # nice if we could do this at compile time but the typing is very funky.
        # What we'd want to assert is that the instance attribute `traits` is an
        # enum of what `valid_traits` below produces. We would want to declare
        # this type in `BaseFactory` and apply to each subclass in the context
        # of the subclass. It doesn't seem like this is possible in Python and
        # therefore we need to do a runtime check. Given that this is only class
        # used in the context of testing this is ok
        valid_traits = [
            name
            for name, value in self.__class__.__dict__.items()
            if isinstance(value, property) and name != "default_attributes"
        ]
        if not set(self.factory_traits).issubset(valid_traits):
            raise TypeError(
                f"traits ({self.factory_traits}) must be a subset of the set of valid traits ({valid_traits})"
            )

    @classmethod
    def _attach_del(cls, obj: Any) -> None:
        """
        Attaches a custom __del__ method to the given object's class.

        This method creates a temporary subclass of the given object's class,
        overriding the __del__ method with a custom implementation defined in
        the cls.__del_override__ method. The object's class is then set to this
        temporary subclass, ensuring that the custom __del__ method is called
        when the object is deleted.

        We need to do this on the class instead of the object because when an
        object is deleted/destroyed, Python looks up the __del__ method on the
        class of the object instead of th object itself. So just attaching it on
        the object itself doesn't work.

        Args:
            obj (Any): The object to which the custom __del__ method will be attached.
        """
        TempSubclass = type(
            "TempSubclass",
            (obj.__class__,),  # inherit from the original class
            {"__del__": cls.__del_override__},  # override __del__
        )
        obj.__class__ = TempSubclass

    @property
    def default_attributes(self) -> dict[str, Any]:
        return {}

    @property
    def attributes(self) -> dict[str, Any]:
        return reduce(
            lambda acc, el: {**acc, **getattr(self, el)},
            self.factory_traits,
            self.default_attributes,
        )

    @staticmethod
    def __del_override__(_self: Any) -> None:
        """
        Custom __del__ method to be overridden in subclasses.

        This method is intended to be overridden in subclasses to provide custom
        cleanup behavior when an object returned by the factory is deleted.
        The method is called when the object is about to be destroyed, allowing
        for any necessary cleanup tasks to be performed.

        Args:
            _self (Any): The instance of the object being deleted.
        """
        pass
