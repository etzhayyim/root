from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalCementState(TypedDict):
    product_name: str
    iso_compliance: bool
    compressive_strength: float
    status: str

def validate_material(state: DentalCementState):
    if state['compressive_strength'] < 50.0:
        return {'status': 'Rejected: Below standard strength'}
    return {'status': 'Validated: Meets ISO 9917'}

graph = StateGraph(DentalCementState)
graph.add_node('validation', validate_material)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
