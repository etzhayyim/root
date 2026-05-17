from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DrillBushState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_dimensions(state: DrillBushState):
    errors = []
    if state['spec_data'].get('hardness_hrc', 0) < 60:
        errors.append('Hardness below industrial standard for drill bushings.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def process_bushings(state: DrillBushState):
    print('Processing procurement specs for Drill Bushings...')
    return state

graph = StateGraph(DrillBushState)
graph.add_node('validate', validate_dimensions)
graph.add_node('process', process_bushings)
graph.add_edge('process', 'validate')
graph.add_edge('validate', END)
graph.set_entry_point('process')
graph = graph.compile()