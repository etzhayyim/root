from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specifications: dict
    validation_status: bool

def validate_specs(state: ProcurementState):
    required = ['Material durability', 'Dimensions']
    valid = all(k in state['specifications'] for k in required)
    return {'validation_status': valid}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()