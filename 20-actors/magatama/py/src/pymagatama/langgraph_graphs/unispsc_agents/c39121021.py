from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ServoState):
    errors = []
    if state['specs'].get('rated_power_kw', 0) <= 0:
        errors.append('Invalid power rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
