from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TitanState(TypedDict):
    part_id: str
    specs: dict
    compliance_cleared: bool
    qc_passed: bool

def validate_specs(state: TitanState):
    # Simulate CAD and material specification validation logic
    state['compliance_cleared'] = 'grade' in state['specs']
    return state

def run_ndt_inspection(state: TitanState):
    # Workflow step for non-destructive testing verification
    state['qc_passed'] = True
    return state

graph = StateGraph(TitanState)
graph.add_node('validate', validate_specs)
graph.add_node('inspection', run_ndt_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspection')
graph.add_edge('inspection', END)
graph = graph.compile()