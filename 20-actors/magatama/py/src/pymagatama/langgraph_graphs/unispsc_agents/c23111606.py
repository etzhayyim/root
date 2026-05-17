from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorProcurementState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: CompressorProcurementState):
    pressure = state['spec_data'].get('pressure', 0)
    state['is_compliant'] = pressure > 0
    return state

def approval_step(state: CompressorProcurementState):
    print(f'Compliance status: {state['is_compliant']}')
    return state

graph = StateGraph(CompressorProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()