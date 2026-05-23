from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HydrotalciteState(TypedDict):
    purity: float
    safety_check: bool
    compliance_report: str

def validate_specs(state: HydrotalciteState):
    if state['purity'] < 98.0:
        return {'compliance_report': 'REJECTED: Purity below 98%'}
    return {'compliance_report': 'APPROVED: Purity meets specs'}

def safety_gate(state: HydrotalciteState):
    state['safety_check'] = True
    return state

graph = StateGraph(HydrotalciteState)
graph.add_node('validation', validate_specs)
graph.add_node('safety', safety_gate)
graph.set_entry_point('safety')
graph.add_edge('safety', 'validation')
graph.add_edge('validation', END)
graph = graph.compile()
