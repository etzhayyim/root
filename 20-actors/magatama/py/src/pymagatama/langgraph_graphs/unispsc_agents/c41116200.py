from typing import TypedDict
from langgraph.graph import StateGraph, END

class POCTState(TypedDict):
    device_id: str
    compliance_docs: list
    validation_passed: bool

def validate_specs(state: POCTState):
    # Simulate validation logic for clinical diagnostic equipment
    state['validation_passed'] = all(d.endswith('.pdf') for d in state['compliance_docs'])
    print(f'Validation result for {state['device_id']}: {state['validation_passed']}')
    return 'end'

graph = StateGraph(POCTState)
graph.add_node('validate_specifications', validate_specs)
graph.set_entry_point('validate_specifications')
graph.add_edge('validate_specifications', END)
graph = graph.compile()
