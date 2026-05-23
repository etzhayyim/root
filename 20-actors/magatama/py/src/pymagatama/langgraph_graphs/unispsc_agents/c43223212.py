from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PagingTerminalState(TypedDict):
    device_id: str
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_frequency(state: PagingTerminalState):
    freq = state['specs'].get('frequency_range_mhz', 0)
    if not (136 <= freq <= 940):
        state['errors'].append('Frequency outside standard band')
        state['validation_passed'] = False
    return state

def check_compliance(state: PagingTerminalState):
    if 'encryption_standard' not in state['specs']:
        state['errors'].append('Missing encryption standard')
        state['validation_passed'] = False
    return state

graph = StateGraph(PagingTerminalState)
graph.add_node('freq_check', validate_frequency)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('freq_check')
graph.add_edge('freq_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
