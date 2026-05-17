from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnchorState(TypedDict):
    anchor_type: str
    pull_out_force: float
    spec_compliance: bool

def validate_anchor_specs(state: AnchorState):
    state['spec_compliance'] = state['pull_out_force'] >= 500.0
    return state

def report_status(state: AnchorState):
    print(f'Compliance status: {state['spec_compliance']}')
    return {'spec_compliance': state['spec_compliance']}

graph = StateGraph(AnchorState)
graph.add_node('validate', validate_anchor_specs)
graph.add_node('report', report_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()