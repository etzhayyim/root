from langgraph.graph import StateGraph, END
from typing import TypedDict

class AircraftSysState(TypedDict):
    part_number: str
    certification_docs: list
    safety_check_passed: bool

def validate_certification(state: AircraftSysState):
    state['safety_check_passed'] = len(state['certification_docs']) > 0
    return 'check_complete'

def finalize_procurement(state: AircraftSysState):
    return 'ready_for_purchase' if state['safety_check_passed'] else 'flag_for_review'

graph = StateGraph(AircraftSysState)
graph.add_node('validate', validate_certification)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()