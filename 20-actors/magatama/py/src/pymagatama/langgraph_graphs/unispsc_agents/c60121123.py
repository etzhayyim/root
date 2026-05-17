from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaperStockState(TypedDict):
    material_type: str
    gsm: int
    inspection_passed: bool

def validate_paper_quality(state: PaperStockState):
    if state['gsm'] > 0:
        return {'inspection_passed': True}
    return {'inspection_passed': False}

def route_by_quality(state: PaperStockState):
    return 'process_order' if state['inspection_passed'] else 'flag_for_review'

graph = StateGraph(PaperStockState)
graph.add_node('validate', validate_paper_quality)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_quality, {'process_order': END, 'flag_for_review': END})
graph.compile()