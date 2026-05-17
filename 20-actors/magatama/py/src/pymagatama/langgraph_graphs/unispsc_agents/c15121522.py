from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AerospaceTitaniumState(TypedDict):
    material_grade: str
    spec_compliance: bool
    inspection_logs: List[str]
    validation_passed: bool

def validate_grade(state: AerospaceTitaniumState) -> AerospaceTitaniumState:
    # Logic to validate Titanium Grade 5 (Ti-6Al-4V) or equivalent aerospace standards
    if state['material_grade'] in ['Grade 5', 'Grade 23']:
        state['validation_passed'] = True
        state['inspection_logs'].append('Grade validation successful')
    else:
        state['validation_passed'] = False
        state['inspection_logs'].append('Grade validation failed')
    return state

def check_compliance(state: AerospaceTitaniumState) -> AerospaceTitaniumState:
    if state['validation_passed']:
        state['spec_compliance'] = True
    return state

graph = StateGraph(AerospaceTitaniumState)
graph.add_node('validate', validate_grade)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()