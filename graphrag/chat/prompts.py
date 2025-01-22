DIMENTION_EXTRACTION = """

    You are tasked with extracting a list of candidate dimensions for data analytics. A 'dimension' is typically something you expect on the x-axis of a graph or the columns of a table.

    Inputs:
        1. A user query: {user_query}
        2. A response to the user query: {response}
        3. A JSON dump representing a list of entities and their properties: {json_schema}

    Your response should be a JSON object in the form of a list of candidates for dimensions. For each candidate, mention the object (one of the entity types in the JSON dump), up to 5 values that adhere to this object (either from the query response or through extrapolation), and a ranking of how relevant this dimension is relative to the other candidates. Provide up to 5 candidates. All responses should be derived from the user query or response.

    Example 1:
    User Query: Tell me about my sales performance in 2024 in the Boston venue
    Response: 
            In 2024, Anaconda Automotive's Boston flagship location achieved impressive sales figures, contributing to the broader success of the dealership network. The Boston venue    
            sold a total of 8,156 units, which was a vital part of Anaconda's overall sales total of 48,932 units, marking a 16.8% increase from the previous year.                       

                                                                                    Monthly Breakdown of Sales                                                                          

            The sales in Boston were diversified across various vehicle categories, indicating strong consumer preferences. Here's the breakdown:                                         

            • Compact SUVs: 3,418 units                                                                                                                                                  
            • Mid-size Sedans: 1,508 units                                                                                                                                               
            • Luxury Sedans: 1,478 units The significant interest in compact SUVs aligns with national trends favoring SUVs and crossovers among consumers.                              

                                                                                Customer Engagement and Challenges                                                                      

            Despite these strong sales numbers, the Boston store faced challenges, particularly around customer engagement in mid-2024. In May, the venue experienced a drop in customer  
            activity due to issues related to warranty claims mishandling, causing customer retention to fall from 65% to 42% by June. To address these challenges, Anaconda Automotive   
            implemented several strategies focused on improving customer service and introduced digital service tracking systems. These initiatives were instrumental in recovering       
            customer satisfaction and retention rates by the end of the year.                                                                                                             

                                                                                            Conclusion                                                                                  

            Overall, Anaconda Automotive's sales performance in Boston during 2024 reflects a strong market presence, despite the challenges related to customer trust and engagement. The
            dealership's responsiveness to these challenges will be crucial for sustaining growth and enhancing customer loyalty moving forward. 
    JSON Dump: 

        {{
            "Customer": {{
                "id": "int",
                "human_readable_id": "int",
                "name": "str",
                "city": "str",
                "state": "str",
                "car_make": "str",
                "car_model": "str",
                "car_trim": "str",
                "mileage": "int"
            }},
            "VehicleModel": {{
                "id": "int",
                "human_readable_id": "int",
                "make": "str",
                "model": "str",
                "trim": "Optional[str]",
                "segment": "Optional[str]",
                "features": "Optional[List[str]]"
            }},
            "CustomerReviewOfVehicle": {{
                "id": "int",
                "human_readable_id": "int",
                "rating": "float",
                "car_make": "str",
                "car_model": "str",
                "car_trim": "str",
                "pros": "Optional[List[str]]",
                "cons": "Optional[List[str]]",
                "sentiment": "str"
            }},
            "DealershipVenue": {{
                "id": "int",
                "human_readable_id": "int",
                "city": "str",
                "company_name": "str",
                "revenue_per_sqft": "Optional[float]",
                "annual_units_sold": "Optional[int]",
                "year": "Optional[int]",
                "is_strategic_location": "Optional[bool]",
                "notes": "Optional[str]"
            }},
            "DealerNetwork": {{
                "id": "int",
                "human_readable_id": "int",
                "name": "str",
                "region": "Optional[str]",
                "specialization": "Optional[str]",
                "service_features": "Optional[List[str]]"
            }},
            "Insight": {{
                "id": "int",
                "human_readable_id": "int",
                "title": "str",
                "description": "str",
                "category": "str",
                "year": "Optional[int]",
                "region": "Optional[str]",
                "market_share": "Optional[float]",
                "risk_factors": "Optional[List[str]]",
                "trends": "Optional[List[str]]",
                "impact_areas": "Optional[List[str]]"
            }},
            "SalesMetric": {{
                "id": "int",
                "human_readable_id": "int",
                "metric_name": "str",
                "time_period": "str",
                "value": "float",
                "unit": "str",
                "category": "str",
                "notes": "Optional[str]"
            }},
            "VehicleCategory": {{
                "id": "int",
                "human_readable_id": "int",
                "name": "str",
                "description": "Optional[str]",
                "price_range_min": "Optional[float]",
                "price_range_max": "Optional[float]",
                "market_share": "Optional[float]",
                "year_over_year_growth": "Optional[float]",
                "average_transaction_price": "Optional[float]",
                "trends": "Optional[List[str]]",
                "year": "Optional[int]"
            }},
            "MonthYear": {{
                "id": "int",
                "human_readable_id": "int",
                "month": "str",
                "year": "int",
                "sales_volume": "int",
                "market_share": "float",
                "average_transaction_price": "float",
                "year_over_year_growth": "float"
            }}
        }}
    Output: [{{'MonthYear', ['Jan2024', 'Feb2024', 'Mar2024', 'Apr2024', 'May2024'], 90}}, {{'DealershipVenue', ['Boston', 'Cleveland', 'Pittsburgh'], 85}}, {{'VehicleCategory', ['Compact SUV','Mid-size sedan', 'Luxury Sedan'],78}}, {{'CustomerReviewOfVehicle',['issues related to warranty claims mishandling'],60}},{{'Insight',['improving customer service and introduced digital service tracking systems'],50}}]

    Example 2:
    User Query: What are the customer satisfaction trends for the past year?
    Response: 
            Customer satisfaction has shown a steady increase over the past year, with notable improvements in Q3 and Q4. The satisfaction score rose from 3.5 in Q1 to 4.2 in Q4. 
            This trend indicates a positive response to the new customer service initiatives implemented in mid-2023, which focused on enhancing the customer experience through personalized service and faster response times.
            The improvements were most significant in the Boston and New York venues, where customer feedback highlighted the effectiveness of these changes.
    JSON Dump: 
        {{
            "Customer": {{
                "id": "int",
                "human_readable_id": "int",
                "name": "str",
                "city": "str",
                "state": "str",
                "car_make": "str",
                "car_model": "str",
                "car_trim": "str",
                "mileage": "int"
            }},
            "CustomerSatisfaction": {{
                "id": "int",
                "human_readable_id": "int",
                "score": "float",
                "quarter": "str",
                "year": "int",
                "venue": "str",
                "feedback": "Optional[str]"
            }}
        }}
    Output: [
        {{
            "dimension": "Quarter",
            "values": ["Q1", "Q2", "Q3", "Q4"],
            "relevance": 95
        }},
        {{
            "dimension": "CustomerSatisfaction",
            "values": ["3.5", "3.8", "4.0", "4.2"],
            "relevance": 90
        }},
        {{
            "dimension": "Venue",
            "values": ["Boston", "New York"],
            "relevance": 85
        }}
    ]

    Example 3:
    User Query: How did the different vehicle categories perform in 2024?
    Response: 
            In 2024, compact SUVs led the sales with 3,418 units, followed by mid-size sedans with 1,508 units, and luxury sedans with 1,478 units. 
            The demand for compact SUVs was driven by their fuel efficiency and versatility, appealing to a broad range of consumers. 
            Mid-size sedans maintained a steady market presence, while luxury sedans saw a slight decline due to increased competition from new electric vehicle models.
            The sales data also revealed a growing interest in hybrid models across all categories, reflecting a shift towards more sustainable vehicle options.
    JSON Dump: 
        {{
            "VehicleCategory": {{
                "id": "int",
                "human_readable_id": "int",
                "name": "str",
                "description": "Optional[str]",
                "sales_units": "int",
                "year": "int",
                "trends": "Optional[List[str]]"
            }},
            "SalesVolume": {{
                "id": "int",
                "human_readable_id": "int",
                "category": "str",
                "units_sold": "int",
                "year": "int"
            }}
        }}
    Output: [
        {{
            "dimension": "VehicleCategory",
            "values": ["Compact SUVs", "Mid-size Sedans", "Luxury Sedans"],
            "relevance": 92
        }},
        {{
            "dimension": "SalesVolume",
            "values": ["3,418", "1,508", "1,478"],
            "relevance": 88
        }},
        {{
            "dimension": "Trend",
            "values": ["Fuel Efficiency", "Hybrid Models"],
            "relevance": 80
        }}
    ]

    Use these examples to guide your extraction process.


"""
