from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeaterSpecState(TypedDict):
    voltage: float
    wattage: float
    compliance_docs: list
    is_approved: bool

def validate_electrical_specs(state: HeaterSpecState):
    state['is_approved'] = state['voltage'] > 0 and state['wattage'] > 0
    return 'validate_electrical_specs'

def check_compliance(state: HeaterSpecState):
    if len(state['compliance_docs']) < 2:
        state['is_approved'] = False
    return 'check_compliance'

graph = StateGraph(HeaterSpecState)
graph.add_node('validate_electrical_specs', validate_electrical_specs)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_electrical_specs', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_electrical_specs')
graph = graph.compile()
