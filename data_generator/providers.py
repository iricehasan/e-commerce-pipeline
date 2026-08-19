from collections import OrderedDict
from faker.providers import BaseProvider

class ProductCategoryProvider(BaseProvider):
    # Using OrderedDict to have different weights
    # Faker doesn't accept normal dict
    _weights = OrderedDict(
        [
            ("electronics", 0.20),
            ("clothing", 0.25),
            ("home", 0.20),
            ("books", 0.15),
            ("toys", 0.10),
            ("beauty", 0.10),
        ]
    )
    
    def product_category(self) -> str:
        return self.random_elements(elements=self._weights, length=1, use_weighting=True)[0]
    
class OrderStatusProvider(BaseProvider):
    _weights = OrderedDict(
        [
            ("pending", 0.05),
            ("shipped", 0.10),
            ("delivered", 0.75),
            ("cancelled", 0.05),
            ("refunded", 0.05),
        ]
    )

    def order_status(self) -> str:
        return self.random_elements(elements=self._weights, length=1, use_weighting=True)[0]