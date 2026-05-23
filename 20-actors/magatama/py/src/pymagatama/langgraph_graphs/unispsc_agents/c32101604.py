from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PROMState(TypedDict):
    part_number: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: PROMState) -> PROMState:
    required = ['capacity', 'voltage', 'temp_range']
    state['validation_passed'] = all(k in state['specs'] for k in required)
    state['log'].append('Technical specs validated successfully.' if state['validation_passed'] else 'Validation failed.')
    return state

def check_export_control(state: PROMState) -> PROMState:
    if state['specs'].get('is_military_grade'):
        state['log'].append('Flagged for dual-use export control review.')
        state['validation_passed'] = False
    return state

graph = StateGraph(PROMState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
