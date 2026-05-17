from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrayState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: TrayState):
    required = ['material_composition', 'dimensions']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid, 'validation_log': ['Specs checked'] if valid else ['Missing data']}

def route_by_compliance(state: TrayState):
    return 'validate' if not state.get('is_compliant') else END

graph = StateGraph(TrayState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()