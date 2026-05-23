from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReportCoverState(TypedDict):
    material: str
    size: str
    compliance_checked: bool

def validate_specs(state: ReportCoverState):
    state['compliance_checked'] = state['material'] in ['Polypropylene', 'Paper', 'Cardstock']
    print('Validation complete')
    return state

graph = StateGraph(ReportCoverState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
