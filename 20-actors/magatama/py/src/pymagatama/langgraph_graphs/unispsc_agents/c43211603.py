from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PortReplicatorState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PortReplicatorState):
    errors = []
    if state['specs'].get('wattage', 0) < 60:
        errors.append('Insufficient power delivery for workstations')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(PortReplicatorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()