from typing import TypedDict
from langgraph.graph import StateGraph, END

class SheaveState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_load_capacity(state: SheaveState):
    capacity = state['spec_data'].get('load_capacity_kg', 0)
    valid = capacity > 0
    return {'validation_passed': valid, 'error_log': [] if valid else ['Invalid load capacity']}

def check_groove_specs(state: SheaveState):
    if 'groove_profile' not in state['spec_data']:
        return {'validation_passed': False, 'error_log': ['Missing groove profile']}
    return {'validation_passed': True}

graph = StateGraph(SheaveState)
graph.add_node('validate_load', validate_load_capacity)
graph.add_node('check_groove', check_groove_specs)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_groove')
graph.add_edge('check_groove', END)
compiled_graph = graph.compile()
