from typing import TypedDict
from langgraph.graph import StateGraph, END

class RelayState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: RelayState):
    required = ['Voltage', 'Current', 'CoilVoltage']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core electrical specs'}

def safety_check(state: RelayState):
    if state['validated'] and 'UL' in state['specs'].get('certifications', []):
        return {'status': 'Approved'}
    return {'status': 'Pending Verification'}

graph = StateGraph(RelayState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
