from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ActivitySetState(TypedDict):
    material: str
    safety_check: bool
    compliance_docs: List[str]

def validate_materials(state: ActivitySetState):
    state['safety_check'] = state['material'] == 'non-toxic'
    return state

def verify_compliance(state: ActivitySetState):
    state['compliance_docs'].append('ASTM_F963_CERT')
    return state

graph = StateGraph(ActivitySetState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', verify_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()