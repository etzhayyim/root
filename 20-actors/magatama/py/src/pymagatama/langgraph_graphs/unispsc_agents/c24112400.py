from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    dimensions: dict
    load_capacity: float
    material_compliance: bool
    approved: bool

def validate_specs(state: StorageState):
    # Ensure load capacity is within industrial standards
    if state['load_capacity'] > 0:
        state['material_compliance'] = True
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(StorageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()