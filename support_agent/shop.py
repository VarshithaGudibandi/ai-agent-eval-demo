from typing import Any

# The demo shop: what each order holds, where it is, and what has come back to the warehouse.

ORDERS: dict[str, dict[str, Any]] = {
    "ord_2001": {"items": {"headphones": 59.0}, "status": "delivered"},
    "ord_2002": {"items": {"blender": 45.0}, "status": "delivered"},
    "ord_2003": {"items": {"backpack": 80.0}, "status": "delivered"},
    "ord_2004": {"items": {"running shoes": 90.0, "socks": 12.0}, "status": "delivered"},
    "ord_2005": {"items": {"keyboard": 70.0, "mouse": 25.0}, "status": "delivered"},
    "ord_2006": {"items": {"desk lamp": 34.5}, "status": "shipped"},
    "ord_2007": {"items": {"office chair": 150.0}, "status": "processing"},
    "ord_2008": {"items": {"camera": 320.0}, "status": "delivered"},
    "ord_2009": {"items": {"phone case": 18.0}, "status": "delivered"},
    "ord_2010": {"items": {"mug": 9.0, "kettle": 30.0, "teapot": 22.0}, "status": "delivered"},
    "ord_2011": {"items": {"water bottle": 15.0}, "status": "delivered"},
    "ord_2012": {"items": {"rain jacket": 70.0}, "status": "delivered"},
}
RETURNS: dict[str, list[str]] = {
    "ord_2001": ["headphones"],
    "ord_2002": ["blender"],
    "ord_2003": [],
    "ord_2004": ["socks"],
    "ord_2005": ["mouse"],
    "ord_2009": [],
    "ord_2012": ["rain jacket"],
}
# Refunds already paid, so a customer asking where theirs is can be told.
REFUNDED: dict[str, float] = {"ord_2002": 45.0}
