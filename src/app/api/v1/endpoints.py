# src/app/api/v1/endpoints.py
"""API V1 Endpoints Module.

This module contains all the endpoint handlers for the v1 API.
It defines the core business logic for handling HTTP requests.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.item import Item, ItemCreate

router = APIRouter()

# In-memory storage for items
items: list[Item] = []


@router.get("/items/", response_model=list[Item], tags=["items"])
async def read_items() -> list[Item]:
    """Retrieve all items.

    Returns:
        List[Item]: A list of all items in the system.

    Example:
        Response:
        ```json
        [
            {
                "id": 1,
                "title": "Item 1",
                "description": "Description for item 1"
            }
        ]
        ```

    """
    return items


@router.post("/items/", response_model=Item, tags=["items"])
async def create_item(item: ItemCreate) -> Item:
    """Create a new item.

    Args:
        item (ItemCreate): The item data to create.

    Returns:
        Item: The created item with its assigned ID.

    Raises:
        HTTPException: If the item data is invalid.

    Example:
        Request:
        ```json
        {
            "title": "New Item",
            "description": "Description for new item"
        }
        ```

    """
    new_item = Item(id=len(items) + 1, **item.model_dump())
    items.append(new_item)
    return new_item


@router.get("/items/{item_id}", response_model=Item, tags=["items"])
async def read_item(item_id: int) -> Item:
    """Retrieve a specific item by its ID.

    Args:
        item_id (int): The ID of the item to retrieve.

    Returns:
        Item: The requested item.

    Raises:
        HTTPException: If the item is not found.

    Example:
        Response:
        ```json
        {
            "id": 1,
            "title": "Item 1",
            "description": "Description for item 1"
        }
        ```

    """
    if item_id < 0 or item_id >= len(items):
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    return items[item_id - 1]
