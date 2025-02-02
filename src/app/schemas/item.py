"""Item Schemas Module.

This module defines Pydantic models for item-related data structures.
These models are used for request/response validation and serialization.
"""

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Base schema for items with common attributes.

    Attributes:
        title (str): The title of the item
        description (Optional[str]): An optional description of the item

    """

    title: str = Field(..., description="The title of the item", min_length=1, examples=["My First Item"])
    description: str | None = Field(
        None, description="An optional description of the item", examples=["A detailed description of my item"]
    )


class ItemCreate(ItemBase):
    """Schema for creating a new item.

    Inherits all attributes from ItemBase.
    """

    pass


class Item(ItemBase):
    """Schema for a complete item, including its ID.

    Attributes:
        id (int): The unique identifier of the item

    """

    id: int = Field(..., description="The unique identifier of the item", gt=0, examples=[1])

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {"id": 1, "title": "Example Item", "description": "This is an example item"},
            "title": "Item Schema",
            "description": "A schema representing an item in the system",
        },
    )
