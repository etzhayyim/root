from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcessingState(TypedDict):
    raw_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_purity(state: ProcessingState) -> ProcessingState:
    purity = state['raw_data'].get('purity_percent', 0)
    if purity < 95.0:
        state['validation_errors'].append('Purity below 95% threshold')
        state['is_compliant'] = False
    return state

def check_microbial(state: ProcessingState) -> ProcessingState:
    if not state['raw_data'].get('microbial_safe', False):
        state['validation_errors'].append('Microbial test failed')
        state['is_compliant'] = False
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_microbial', check_microbial)

graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_microbial')
graph.add_edge('check_microbial', END)
graph = graph.compile()