from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CleaningSpecs(TypedDict):
    material_type: str
    compliance_codes: List[str]
    is_verified: bool

def validate_cleaning_standards(state: CleaningSpecs):
    required = ['ISO_15883', 'FDA_CLEARED']
    state['is_verified'] = all(code in state['compliance_codes'] for code in required)
    return state

def check_material_safety(state: CleaningSpecs):
    if state['material_type'] == 'aluminium' and 'corrosion_inhibitor' not in state.get('compliance_codes', []):
        state['is_verified'] = False
    return state

graph = StateGraph(CleaningSpecs)
graph.add_node('validate', validate_cleaning_standards)
graph.add_node('safety_check', check_material_safety)
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
