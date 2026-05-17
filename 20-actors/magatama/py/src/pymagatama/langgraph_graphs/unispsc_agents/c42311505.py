from typing import TypedDict
from langgraph.graph import StateGraph, END

class BandageState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_sterility(state: BandageState):
    is_sterile = state['specs'].get('sterility_cert') is not None
    return {'is_compliant': is_sterile, 'validation_log': ['Sterility check passed'] if is_sterile else ['Sterility cert missing']}

def check_expiry(state: BandageState):
    expiry = state['specs'].get('expiry_date')
    return {'validation_log': state['validation_log'] + ['Expiry date verified']}

graph = StateGraph(BandageState)
graph.add_node('validate', validate_sterility)
graph.add_node('expiry', check_expiry)
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('validate')
graph = graph.compile()