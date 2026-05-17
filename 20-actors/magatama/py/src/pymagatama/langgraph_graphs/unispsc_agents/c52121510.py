from typing import TypedDict
from langgraph.graph import StateGraph, END

class BeddingState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_spec(state: BeddingState):
    required = ['material', 'flame_retardancy', 'dimensions']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def check_fire_safety(state: BeddingState):
    if state.get('spec_data', {}).get('flame_retardancy') == 'certified':
        return 'compliant'
    return 'non_compliant'

graph = StateGraph(BeddingState)
graph.add_node('validate', validate_spec)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
# Graph initialized for standard bedding procurement workflow.