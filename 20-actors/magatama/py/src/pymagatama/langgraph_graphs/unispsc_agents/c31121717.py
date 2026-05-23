from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validation_passed: bool
    export_flag: bool

def validate_specs(state: CastingState):
    # Simulate CAD and material validation logic
    state['validation_passed'] = all(k in state['specs'] for k in ['material', 'tolerance'])
    print('Validating casting specifications...')
    return state

def check_dual_use(state: CastingState):
    # Simulate export control screening
    state['export_flag'] = state['specs'].get('industry') == 'Aerospace'
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
