from typing import TypedDict
from langgraph.graph import StateGraph, END
class SurgicalGloveState(TypedDict):
    material: str
    aql_score: float
    is_sterile: bool
    compliance_ok: bool
def validate_specs(state: SurgicalGloveState):
    state['compliance_ok'] = state['aql_score'] <= 1.5 and state['is_sterile']
    return state
graph = StateGraph(SurgicalGloveState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()