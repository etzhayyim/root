from typing import TypedDict
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_control_check: bool

def validate_metadata(state: TitaniumState):
    state['validation_passed'] = all(k in state['spec_data'] for k in ['grade', 'tolerance'])
    print('Validating titanium specs...')
    return {'validation_passed': state['validation_passed']}

def export_control_check(state: TitaniumState):
    state['export_control_check'] = state['spec_data'].get('destination') != 'restricted'
    return {'export_control_check': state['export_control_check']}

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_metadata)
graph.add_node('export', export_control_check)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
process = graph.compile()