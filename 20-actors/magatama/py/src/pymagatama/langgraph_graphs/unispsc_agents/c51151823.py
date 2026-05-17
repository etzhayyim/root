from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_passed: bool

def validate_purity(state: DrugState):
    state['compliance_passed'] = state['purity_level'] >= 99.5
    return state

def check_certification(state: DrugState):
    print(f'Verifying CoA for {state['batch_id']}')
    return state

graph = StateGraph(DrugState)
graph.add_node('validate', validate_purity)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()