from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ZincExtrusionState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ZincExtrusionState):
    errors = []
    if state['spec_data'].get('alloy') != 'ASTM B86':
        errors.append('Invalid alloy grade')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: ZincExtrusionState):
    if state['validation_passed']:
        print('Procurement spec validated successfully.')
    return state

graph = StateGraph(ZincExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
app = graph.compile()
