from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DressingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_sterility(state: DressingState):
    """Ensures the dressing meets medical sterile standards."""
    if 'sterilization_method' not in state['spec_data']:
        state['validation_errors'].append('Missing sterilization data')
    return state

def check_regulatory(state: DressingState):
    """Checks compliance with health authority certifications."""
    if 'iso_cert' not in state['spec_data']:
        state['validation_errors'].append('Missing ISO 13485 certification')
    return state

graph = StateGraph(DressingState)
graph.add_node('sterility', validate_sterility)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('sterility')
graph.add_edge('sterility', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
