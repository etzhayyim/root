from typing import TypedDict
from langgraph.graph import StateGraph, END

class CotSystemState(TypedDict):
    spec_data: dict
    validated: bool
    safety_report: str

def validate_safety_standards(state: CotSystemState):
    cert = state['spec_data'].get('safety_certification_standard')
    state['validated'] = cert in ['ASTM-F963', 'EN-71']
    return state

def check_hazard_testing(state: CotSystemState):
    if state['validated']:
        state['safety_report'] = 'PASS: Safety standards verified.'
    else:
        state['safety_report'] = 'FAIL: Missing or invalid certification.'
    return state

graph = StateGraph(CotSystemState)
graph.add_node('validate', validate_safety_standards)
graph.add_node('check', check_hazard_testing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()