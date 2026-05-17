from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PathState(TypedDict):
    location: str
    material_specs: List[str]
    compliance_checklist: List[str]
    approved: bool

def validate_materials(state: PathState):
    # Simulate material compliance check
    state['approved'] = all('standard' in spec.lower() for spec in state['material_specs'])
    return state

def check_compliance(state: PathState):
    # Simulate accessibility compliance
    state['compliance_checklist'].append('ADA_COMPLIANT')
    return state

graph = StateGraph(PathState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()