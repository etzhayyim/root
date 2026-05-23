from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ClayProcessState(TypedDict):
    material_safety_data: str
    quality_check_passed: bool
    compliance_tags: List[str]

def validate_safety(state: ClayProcessState) -> ClayProcessState:
    state['quality_check_passed'] = 'AP' in state['material_safety_data']
    return state

def check_compliance(state: ClayProcessState) -> ClayProcessState:
    state['compliance_tags'] = ['ASTM-D4236'] if state['quality_check_passed'] else []
    return state

graph = StateGraph(ClayProcessState)
graph.add_node('validate', validate_safety)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
