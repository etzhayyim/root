from langgraph.graph import StateGraph, END
from typing import TypedDict
class DryCleanState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_score: float
def validate_solvent_system(state: DryCleanState):
    state['validated'] = state['spec_data'].get('solvent_type') in ['Perchloroethylene', 'Hydrocarbon']
    return state
def assess_safety_compliance(state: DryCleanState):
    state['compliance_score'] = 1.0 if state['spec_data'].get('safety_certified', False) else 0.5
    return state
graph = StateGraph(DryCleanState)
graph.add_node('validate', validate_solvent_system)
graph.add_node('safety', assess_safety_compliance)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
app = graph.compile()