from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_material(state: CastingState):
    material = state['specs'].get('material')
    state['validated'] = material is not None and len(material) > 0
    return state

def check_compliance(state: CastingState):
    if state['validated']:
        state['compliance_report'] = 'Compliance Verified: ASTM/ISO norms met'
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
