from typing import TypedDict
from langgraph.graph import StateGraph, END

class RehabProductState(TypedDict):
    product_id: str
    compliance_docs: list
    validation_passed: bool

def validate_compliance(state: RehabProductState):
    # Simulate logic checking medical certificates
    state['validation_passed'] = len(state['compliance_docs']) > 0
    return state

def check_maintenance(state: RehabProductState):
    print(f'Checking maintenance requirements for {state[product_id]}')
    return state

graph = StateGraph(RehabProductState)
graph.add_node('compliance', validate_compliance)
graph.add_node('maintenance', check_maintenance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'maintenance')
graph.add_edge('maintenance', END)
graph = graph.compile()
