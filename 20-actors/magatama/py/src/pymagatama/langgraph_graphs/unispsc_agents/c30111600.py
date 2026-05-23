from typing import TypedDict
from langgraph.graph import StateGraph, END

class CementState(TypedDict):
    material_type: str
    quality_cert: bool
    compliance_check: bool

def validate_quality(state: CementState):
    state['compliance_check'] = state['quality_cert'] is True
    return state

def check_hazard(state: CementState):
    print(f'Checking storage requirements for {state.get('material_type')}')
    return state

graph = StateGraph(CementState)
graph.add_node('validate', validate_quality)
graph.add_node('safety', check_hazard)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
