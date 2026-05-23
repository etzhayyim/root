from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScaleState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_scale_specs(state: ScaleState):
    required = ['load_capacity', 'accuracy_class', 'calibration_date']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'error': None if valid else 'Missing required fields'}

def compliance_check(state: ScaleState):
    print('Running healthcare compliance check...')
    return {'validated': state['validated']}

graph = StateGraph(ScaleState)
graph.add_node('validate', validate_scale_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
