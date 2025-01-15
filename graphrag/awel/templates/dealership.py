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

class VehicleModel(BaseModel):
    """A vehicle model offered by the dealership."""
    id: int = Field(description="Auto-generated uuid for the vehicle model")
    human_readable_id: int = Field(description="Human-readable id for the vehicle model. Echo it back from the input")
    make: str = Field(description="The manufacturer of the vehicle")
    model: str = Field(description="The model name of the vehicle")
    trim: Optional[str] = Field(default=None, description="The trim level of the vehicle")
    segment: Optional[str] = Field(default=None, description="The market segment of the vehicle (e.g., mid-size SUV)")
    features: Optional[List[str]] = Field(default=None, description="List of notable features of the vehicle")

class ListOfVehicleModels(BaseModel):
    items: List[VehicleModel] = Field(description="A list of vehicle models")

class CustomerReview(BaseModel):
    """A customer review of a vehicle."""
    id: int = Field(description="Auto-generated uuid for the review")
    human_readable_id: int = Field(description="Human-readable id for the review. Echo it back from the input")
    rating: float = Field(description="The rating given by the customer (out of 5.0)")
    car_make: str = Field(description="The make of the reviewed vehicle")
    car_model: str = Field(description="The model of the reviewed vehicle")
    car_trim: str = Field(description="The trim level of the reviewed vehicle")
    pros: Optional[List[str]] = Field(default=None, description="List of positive aspects mentioned in the review")
    cons: Optional[List[str]] = Field(default=None, description="List of negative aspects mentioned in the review")
    sentiment: str = Field(description="Overall sentiment of the review (positive|negative|indifferent)")

class ListOfCustomerReviews(BaseModel):
    items: List[CustomerReview] = Field(description="A list of customer reviews")

class DealershipVenue(BaseModel):
    """A physical dealership location."""
    id: int = Field(description="Auto-generated uuid for the dealership venue")
    human_readable_id: int = Field(description="Human-readable id for the dealership venue. Echo it back from the input")
    city: str = Field(description="The city where the dealership is located")
    company_name: str = Field(description="The name of the dealership company")
    revenue_per_sqft: Optional[float] = Field(default=None, description="Revenue per square foot in USD")
    annual_units_sold: Optional[int] = Field(default=None, description="Number of vehicles sold in a year")
    year: Optional[int] = Field(default=None, description="The year for which the statistics are reported")
    is_strategic_location: Optional[bool] = Field(default=None, description="Whether this is a strategic location")
    notes: Optional[str] = Field(default=None, description="Additional notes about the venue")

class ListOfDealershipVenues(BaseModel):
    items: List[DealershipVenue] = Field(description="A list of dealership venues")

class DealerNetwork(BaseModel):
    """A network of dealerships operating under a common brand or region."""
    id: int = Field(description="Auto-generated uuid for the dealer network")
    human_readable_id: int = Field(description="Human-readable id for the dealer network. Echo it back from the input")
    name: str = Field(description="The name of the dealer network")
    region: Optional[str] = Field(default=None, description="The geographical region where the network operates")
    specialization: Optional[str] = Field(default=None, description="Brand or service specialization of the network")
    service_features: Optional[List[str]] = Field(default=None, description="Notable service features or specialties")

class ListOfDealerNetworks(BaseModel):
    items: List[DealerNetwork] = Field(description="A list of dealer networks")
