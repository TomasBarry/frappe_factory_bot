# Frappe Factory Bot

A powerful factory library for Frappe that makes testing easier and more maintainable. Inspired by [Factory Boy](https://factoryboy.readthedocs.io/en/stable/index.html) and similar factory libraries.

## Why Use Factories?

Factories help eliminate repetitive setup code in tests and make tests more maintainable. Consider this common pattern:

```python
def test_something():
    # Create test data
    individual = frappe.get_doc({
        "doctype": "Individual",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        # ... many more required fields
    })
    individual.insert()

    # Actual test code starts here
    ...
```

This setup code is:
1. Repetitive across tests
2. Brittle - adding/removing fields requires updating many tests
3. Makes tests harder to read with more setup than actual test code

With Frappe Factory Bot, this becomes:

```python
def test_something():
    individual = IndividualFactory.create()
    # Test code starts here
```

## Basic Usage

### Creating a Factory

```python
from frappe_factory_bot.frappe_factory_bot.base_factory import BaseFactory

class StoreFactory(BaseFactory):
    doctype = "Store"  # The Frappe DocType name

    @property
    def default_attributes(self) -> dict[str, Any]:
        """Default values for required fields"""
        return {
            "store_name": "Downtown Store",
            "zip_code": "94105",
            "is_active": 1
        }

    @property
    def with_california_address(self) -> dict[str, Any]:
        """A trait for stores in California"""
        return {
            "state": "CA",
            "country": "United States"
        }
```

### Using Factories

There are four main methods for using factories:

1. `build()` - Creates an unsaved document
```python
store = StoreFactory.build()
store.name  # None (not saved)
```

2. `create()` - Creates and saves a document
```python
store = StoreFactory.create()
store.name  # Auto-generated name
```

3. `build_list()` - Creates multiple unsaved documents
```python
stores = StoreFactory.build_list(3)
# Returns list of 3 unsaved stores
```

4. `create_list()` - Creates and saves multiple documents
```python
stores = StoreFactory.create_list(3)
# Returns list of 3 saved stores
```

### Customizing Factory Output

There are three ways to customize the documents created by factories:

1. Default Attributes - Set in the factory class:
```python
@property
def default_attributes(self) -> dict[str, Any]:
    return {
        "store_name": "Downtown Store"
    }
```

2. Traits - Reusable attribute sets:
```python
@property
def with_california_address(self) -> dict[str, Any]:
    return {
        "state": "CA",
        "country": "United States"
    }

# Usage:
store = StoreFactory.create(traits=["with_california_address"])
```

3. Overrides - One-off customizations:
```python
store = StoreFactory.create(store_name="Custom Store")
```

### Precedence

When multiple sources define the same attribute:
1. Overrides take highest precedence
2. Traits override default attributes
3. Default attributes are used if no other value is specified

```python
store = StoreFactory.create(
    traits=["with_california_address"],
    store_name="Override Name"
)
# store_name will be "Override Name"
```

### Factory Relationships

Factories can create related records. When implementing relationships, it's suggested to handle overrides properly to avoid creating orphaned records:

```python
class OrderFactory(BaseFactory):
    doctype = "Order"

    @property
    def with_customer(self) -> dict[str, Any]:
        # Check for override before creating a new customer
        return {
            "customer": self.overrides.get("customer") or CustomerFactory.create().name
        }

# Usage:
# This creates both an order and a customer
order = OrderFactory.create(traits=["with_customer"])

# This uses an existing customer without creating a new one
existing_customer = CustomerFactory.create()
order = OrderFactory.create(
    traits=["with_customer"],
    customer=existing_customer.name
)
```

This pattern is important because:
1. It prevents creating unnecessary records when an override is provided
2. Makes tests more efficient and cleaner
3. Allows reuse of existing records when needed
4. Avoids orphaned records in the test database

## Best Practices

1. Use meaningful trait names that describe the business concept
2. Keep factories focused on required attributes
3. Use traits for common variations
4. Use faker for generating realistic test data
5. Consider using factory relationships to maintain data consistency
6. Always check for overrides before creating related records

## License

MIT
