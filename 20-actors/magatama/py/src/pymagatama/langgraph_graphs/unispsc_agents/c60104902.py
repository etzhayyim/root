from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectrostaticState(TypedDict):
    voltage_spec: float
    esd_certificate: str
    is_compliant: bool

def validate_esd_specs(state: ElectrostaticState):
    state['is_compliant'] = (state['voltage_spec'] > 0 and state['esd_certificate'] != '')
    return state

def route_by_compliance(state: ElectrostaticState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(ElectrostaticState)
graph.add_node('validate', validate_esd_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()