###
## A set of pydantic definitions for car dealership-related data
###

from typing import List, Optional
from pydantic import BaseModel, Field

class Customer(BaseModel):
    """A dealership customer."""
    id: int = Field(description="Auto-generated uuid for the customer")
    human_readable_id: int = Field(description="Human-readable id for the customer. Echo it back from the input")
    name: str = Field(description="The name of the customer (format: First Last)")
    city: str = Field(description="The city where the customer is from")
    state: str = Field(description="The state where the customer is from")
    car_make: str = Field(description="The make of the car purchased")
    car_model: str = Field(description="The model of the car purchased")
    car_trim: str = Field(description="The trim level of the car purchased")
    mileage: int = Field(description="The number of miles driven by the customer")

class ListOfCustomers(BaseModel):
    items: List[Customer] = Field(description="A list of customers")
