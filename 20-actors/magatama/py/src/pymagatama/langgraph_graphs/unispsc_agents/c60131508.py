from typing import TypedDict
from langgraph.graph import StateGraph, END

class MusicBoxState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_mechanism(state: MusicBoxState):
    mechanism = state['spec_data'].get('mechanism_type')
    results = state.get('validation_results', [])
    if mechanism in ['mechanical', 'digital']:
        results.append('Type validated successfully')
    return {'validation_results': results, 'is_approved': True}

graph = StateGraph(MusicBoxState)
graph.add_node('validate', validate_mechanism)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
