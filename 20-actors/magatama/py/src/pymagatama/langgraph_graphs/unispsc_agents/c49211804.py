from typing import TypedDict
from langgraph.graph import StateGraph, END

class TeamMarkerState(TypedDict):
    material_type: str
    is_reflective: bool
    compliance_checked: bool

def validate_specs(state: TeamMarkerState):
    print('Validating material specifications...')
    state['compliance_checked'] = state.get('material_type') in ['Polyester', 'Nylon']
    return state

def check_visibility(state: TeamMarkerState):
    print('Checking visibility requirements...')
    return {'compliance_checked': state['is_reflective'] or state['compliance_checked']}

graph = StateGraph(TeamMarkerState)
graph.add_node('validate', validate_specs)
graph.add_node('visibility', check_visibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'visibility')
graph.add_edge('visibility', END)
app = graph.compile()
