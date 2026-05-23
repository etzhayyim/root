from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlugState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: PlugState):
    specs = state['spec_data']
    required = ['voltage', 'current', 'safety_cert']
    compliance = all(k in specs for k in required)
    return {'is_compliant': compliance}

workflow = StateGraph(PlugState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
