from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectrophoresisGraphState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_power_specs(state: ElectrophoresisGraphState):
    errors = []
    if state['specs'].get('voltage', 0) > 3000: errors.append('Voltage exceeds safety limit')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ElectrophoresisGraphState)
graph.add_node('validate', validate_power_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()