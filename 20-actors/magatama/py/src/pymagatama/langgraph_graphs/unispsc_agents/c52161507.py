from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RadioState(TypedDict):
    model_number: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: RadioState):
    log = []
    required = ['voltage', 'safety_cert']
    compliant = all(key in state['specs'] for key in required)
    log.append('Specs validated' if compliant else 'Missing mandatory specs')
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(RadioState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
