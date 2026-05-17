from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WoodBeamState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WoodBeamState):
    errors = []
    if state['spec_data'].get('moisture_content', 0) > 20:
        errors.append('Moisture content exceeds 20% limit.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def structural_analysis(state: WoodBeamState):
    if state.get('is_compliant', False):
        print('Performing structural load simulation...')
    return {}

graph = StateGraph(WoodBeamState)
graph.add_node('validate', validate_specs)
graph.add_node('analysis', structural_analysis)
graph.set_entry_point('validate')
graph.add_edge('validate', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()