from typing import TypedDict
from langgraph.graph import StateGraph, END

class DisplayWorkflowState(TypedDict):
    part_number: str
    compliance_docs: list
    validation_status: bool

def validate_aerospace_specs(state: DisplayWorkflowState):
    # Simulate spec validation logic
    state['validation_status'] = len(state['compliance_docs']) >= 2
    return 'validate_aerospace_specs'

def export_control_check(state: DisplayWorkflowState):
    # Dual-use regulatory check
    return 'export_control_check'

graph = StateGraph(DisplayWorkflowState)
graph.add_node('validate', validate_aerospace_specs)
graph.add_node('export', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()