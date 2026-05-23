from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_id: str
    airworthiness_docs: bool
    inspection_passed: bool
    final_status: str

def validate_certification(state: AircraftComponentState):
    state['airworthiness_docs'] = True
    return 'check_inspection'

def perform_quality_check(state: AircraftComponentState):
    state['inspection_passed'] = True
    return 'finalize'

def finalize_process(state: AircraftComponentState):
    state['final_status'] = 'APPROVED'
    return END

graph = StateGraph(AircraftComponentState)
graph.add_node('certify', validate_certification)
graph.add_node('check_inspection', perform_quality_check)
graph.add_node('finalize', finalize_process)
graph.set_entry_point('certify')
graph.add_edge('certify', 'check_inspection')
graph.add_edge('check_inspection', 'finalize')
graph = graph.compile()
