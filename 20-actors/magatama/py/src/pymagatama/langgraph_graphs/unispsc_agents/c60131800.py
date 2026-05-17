from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    # Simulate validation of music/dance accessory specifications
    is_valid = all(key in state['specs'] for key in ['material', 'standard_compliance'])
    return {'approved': is_valid}

def route_procurement(state: ProcurementState):
    return 'approved' if state['approved'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()