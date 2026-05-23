from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: PipeState):
    required_fields = ['material', 'pressure', 'standard']
    state['is_compliant'] = all(k in state['spec_data'] for k in required_fields)
    return state

def route_by_compliance(state: PipeState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(PipeState)
graph.add_node('validation', validate_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph.compile()
