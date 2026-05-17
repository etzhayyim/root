from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IEFState(TypedDict):
    purity_validated: bool
    compliance_check: bool
    steps: List[str]

def validate_purity(state: IEFState):
    state['purity_validated'] = True
    state['steps'].append('Purity Check Completed')
    return state

def run_compliance(state: IEFState):
    state['compliance_check'] = True
    state['steps'].append('Compliance Logged')
    return state

graph = StateGraph(IEFState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', run_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()