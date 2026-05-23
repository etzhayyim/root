from typing import TypedDict
from langgraph.graph import StateGraph, END

class HarnessState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: HarnessState):
    required = ['wire_gauge', 'voltage_rating']
    return {'is_compliant': all(k in state['specs'] for k in required)}

workflow = StateGraph(HarnessState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
