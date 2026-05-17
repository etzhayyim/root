from typing import TypedDict
from langgraph.graph import StateGraph, END

class StaticEliminatorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: StaticEliminatorState):
    s = state['spec_data']
    errors = []
    if s.get('ion_balance_range', 0) > 50: errors.append('Ion balance excessive')
    if not s.get('compliance_standards'): errors.append('Missing safety standards')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

graph = StateGraph(StaticEliminatorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()