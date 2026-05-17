from typing import TypedDict
from langgraph.graph import StateGraph, END

class CuttingMachineState(TypedDict):
    specs: dict
    is_compliant: bool
    error_log: list

def validate_specs(state: CuttingMachineState):
    required = ['laser_power_kw', 'safety_certification']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: CuttingMachineState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(CuttingMachineState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()