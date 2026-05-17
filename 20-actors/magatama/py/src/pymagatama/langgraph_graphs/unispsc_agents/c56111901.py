from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IndustrialComponentState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: IndustrialComponentState):
    # Perform compatibility check for IP rating and voltage support
    state['validated'] = all(k in state['specs'] for k in ['ip_rating', 'voltage'])
    state['compliance_report'] = 'Validated' if state['validated'] else 'Missing required fields'
    return state

graph = StateGraph(IndustrialComponentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()