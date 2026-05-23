from typing import TypedDict
from langgraph.graph import StateGraph, END

class LogicState(TypedDict):
    part_number: str
    spec_sheet_verified: bool
    export_compliance_check: bool

def validate_specs(state: LogicState):
    # Simulate spec validation logic for GAL
    state['spec_sheet_verified'] = True
    return state

def export_review(state: LogicState):
    # Simulate dual-use control check
    print(f'Checking export status for {state['part_number']}')
    state['export_compliance_check'] = True
    return state

graph = StateGraph(LogicState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
