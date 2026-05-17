from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LaboratorySupplyState(TypedDict):
    item_name: str
    specifications: List[str]
    validation_status: str

def validate_anaerobic_specs(state: LaboratorySupplyState):
    required = ['airtight_seal', 'pressure_rating']
    valid = all(s in state['specifications'] for s in required)
    return { 'validation_status': 'PASS' if valid else 'FAIL' }

def approve_procurement(state: LaboratorySupplyState):
    return { 'validation_status': 'APPROVED' }

graph = StateGraph(LaboratorySupplyState)
graph.add_node('validate', validate_anaerobic_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()