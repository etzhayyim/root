from typing import TypedDict
from langgraph.graph import StateGraph, END

class HoneyProcurementState(TypedDict):
    quality_report: dict
    approved: bool

def validate_purity(state: HoneyProcurementState):
    moisture = state['quality_report'].get('moisture', 20)
    state['approved'] = moisture <= 18.0
    return 'check_complete'

def check_residue(state: HoneyProcurementState):
    residue = state['quality_report'].get('pesticide_ppm', 0.0)
    state['approved'] = state['approved'] and (residue < 0.01)
    return 'check_complete'

graph = StateGraph(HoneyProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_residue', check_residue)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_residue')
graph.add_edge('check_residue', END)
graph = graph.compile()
