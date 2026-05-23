from langgraph.graph import StateGraph, END
from typing import TypedDict

class PipeState(TypedDict):
    spec_data: dict
    is_validated: bool

def validate_clamp_specs(state: PipeState):
    specs = state['spec_data']
    valid = all(key in specs for key in ['pressure_rating', 'material_grade'])
    print(f'Validating repair clamp parameters: {specs}')
    return {'is_validated': valid}

def route_verification(state: PipeState):
    return 'valid' if state['is_validated'] else 'error'

graph = StateGraph(PipeState)
graph.add_node('validation', validate_clamp_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
