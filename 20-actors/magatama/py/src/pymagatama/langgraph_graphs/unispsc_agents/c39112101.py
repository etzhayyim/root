from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    is_validated: bool
    validation_errors: List[str]

def validate_specs(state: LightingState):
    errors = []
    if state['spec_data'].get('transmission_loss', 0) > 0.5:
        errors.append('Transmission loss exceeding threshold')
    return {'is_validated': len(errors) == 0, 'validation_errors': errors}

def process_procurement(state: LightingState):
    print('Processing fiber optic lighting order')
    return {'status': 'processed'}

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
