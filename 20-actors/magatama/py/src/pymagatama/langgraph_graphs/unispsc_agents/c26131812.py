from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GISState(TypedDict):
    voltage_kv: float
    gas_check_passed: bool
    compliance_cert: str
    approved: bool

def validate_specs(state: GISState):
    if state['voltage_kv'] > 0 and state['compliance_cert']:
        return {'approved': True}
    return {'approved': False}

def inspect_gas(state: GISState):
    return {'gas_check_passed': True}

graph = StateGraph(GISState)
graph.add_node('validate', validate_specs)
graph.add_node('gas_check', inspect_gas)
graph.set_entry_point('validate')
graph.add_edge('validate', 'gas_check')
graph.add_edge('gas_check', END)
graph = graph.compile()