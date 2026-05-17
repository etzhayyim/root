from langgraph.graph import StateGraph, END
from typing import TypedDict

class AuditState(TypedDict):
    material_spec: str
    quality_score: float
    is_compliant: bool

def validate_die_specs(state: AuditState):
    state['is_compliant'] = state['material_spec'] == 'High-Density Epoxy' and state['quality_score'] > 0.9
    return state

graph = StateGraph(AuditState)
graph.add_node('validate', validate_die_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()