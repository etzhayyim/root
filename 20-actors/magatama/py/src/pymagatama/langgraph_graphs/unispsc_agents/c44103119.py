from langgraph.graph import StateGraph, END
from typing import TypedDict
class TransferPaperState(TypedDict):
    paper_specs: dict
    validation_passed: bool
def validate_specs(state: TransferPaperState):
    required = ['weight', 'melt_temp']
    state['validation_passed'] = all(k in state['paper_specs'] for k in required)
    return {'validation_passed': state['validation_passed']}
def finalize_procurement(state: TransferPaperState):
    return {'status': 'READY_FOR_ORDER'}
graph = StateGraph(TransferPaperState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
