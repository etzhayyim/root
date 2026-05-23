from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ModemState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ModemState):
    errors = []
    if 'protocol' not in state['specs']: errors.append('Missing protocol')
    if 'encryption' not in state['specs']: errors.append('Encryption missing')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ModemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
