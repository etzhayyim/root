from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AerospaceMaterialState(TypedDict):
    material_code: str
    spec_compliance: bool
    inspection_log: List[str]

def validate_material(state: AerospaceMaterialState) -> AerospaceMaterialState:
    state['inspection_log'].append('Validating alloy composition against aerospace standards.')
    state['spec_compliance'] = True
    return state

def check_certification(state: AerospaceMaterialState) -> AerospaceMaterialState:
    state['inspection_log'].append('Verifying ISO9100/AS9100 documentation.')
    return state

graph = StateGraph(AerospaceMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()