from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PrintingPlateState(TypedDict):
    plate_type: str
    spec_compliance: bool
    inspection_result: str

def validate_specs(state: PrintingPlateState):
    state['spec_compliance'] = len(state['plate_type']) > 0
    return state

def run_quality_check(state: PrintingPlateState):
    state['inspection_result'] = 'PASS' if state['spec_compliance'] else 'FAIL'
    return state

graph = StateGraph(PrintingPlateState)
graph.add_node('validate', validate_specs)
graph.add_node('inspection', run_quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspection')
graph.add_edge('inspection', END)
graph = graph.compile()