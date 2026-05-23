from typing import TypedDict
from langgraph.graph import StateGraph, END

class InkProcurementState(TypedDict):
    spec_content: str
    validation_passed: bool
    approved: bool

def validate_ink_specs(state: InkProcurementState):
    # Simulate validation of ink stick specifications
    is_valid = 'carbon' in state['spec_content'].lower()
    return {'validation_passed': is_valid}

def approval_step(state: InkProcurementState):
    return {'approved': state['validation_passed']}

graph = StateGraph(InkProcurementState)
graph.add_node('validate', validate_ink_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
