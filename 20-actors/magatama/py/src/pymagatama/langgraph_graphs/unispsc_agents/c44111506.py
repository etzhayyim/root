from typing import TypedDict
from langgraph.graph import StateGraph, END
class OfficeSupplyState(TypedDict):
    item_name: str
    specs: dict
    approved: bool
def validate_specs(state: OfficeSupplyState):
    required = ['Material', 'Dimensions']
    state['approved'] = all(k in state['specs'] for k in required)
    return state
def finalize_procurement(state: OfficeSupplyState):
    print(f"Processing procurement for {state['item_name']}: Status {state['approved']}")
    return state
builder = StateGraph(OfficeSupplyState)
builder.add_node('validate', validate_specs)
builder.add_node('finalize', finalize_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'finalize')
builder.add_edge('finalize', END)
graph = builder.compile()
