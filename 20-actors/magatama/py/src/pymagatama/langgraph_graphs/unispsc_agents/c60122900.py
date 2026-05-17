from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BeadProcurementState(TypedDict):
    material: str
    quality_index: float
    compliance_docs: List[str]
    approved: bool

def validate_material(state: BeadProcurementState):
    # Business logic for specific bead material checks
    state['approved'] = state['material'] in ['Glass', 'Plastic', 'Metal', 'Wood']
    return state

def inspect_quality(state: BeadProcurementState):
    if state['approved'] and state['quality_index'] > 0.8:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(BeadProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', inspect_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()