from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InsulationState(TypedDict):
    material_type: str
    thermal_resistance: float
    compliance_docs: List[str]
    approved: bool

def validate_insulation(state: InsulationState):
    if state['thermal_resistance'] > 0.0 and len(state['compliance_docs']) > 0:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(InsulationState)
graph.add_node('validate', validate_insulation)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()