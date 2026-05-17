from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    item_list: List[str]
    validation_errors: List[str]
    approved: bool

def validate_supplies(state: OfficeSupplyState):
    errors = [item for item in state['item_list'] if not item.strip()]
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_procurement(state: OfficeSupplyState):
    return 'approved' if state['approved'] else END

builder = StateGraph(OfficeSupplyState)
builder.add_node('validator', validate_supplies)
builder.set_entry_point('validator')
builder.add_conditional_edges('validator', route_procurement, {'approved': END})
graph = builder.compile()