from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RadioState(TypedDict):
    commodity_code: str
    activity_level: float
    safety_clearance: bool
    delivery_route: Sequence[str]

def validate_safety_protocols(state: RadioState):
    # Simulate stringent biohazard and safety checks
    return {'safety_clearance': state['activity_level'] < 500.0}

def route_shipment(state: RadioState):
    return {'delivery_route': ['HazardousMaterialCarrier', 'MedicalInstitution']}

builder = StateGraph(RadioState)
builder.add_node('safety_check', validate_safety_protocols)
builder.add_node('routing', route_shipment)
builder.add_edge('safety_check', 'routing')
builder.add_edge('routing', END)
builder.set_entry_point('safety_check')
graph = builder.compile()