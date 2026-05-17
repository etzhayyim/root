from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicrofilmSpecs(TypedDict):
    device_id: str
    magnification: float
    format_supported: str
    is_verified: bool

def validate_specs(state: MicrofilmSpecs):
    state['is_verified'] = state['magnification'] >= 10.0
    return state

def quality_check(state: MicrofilmSpecs):
    print(f'Checking compatibility for {state['format_supported']}')
    return {'is_verified': state['is_verified']}

graph = StateGraph(MicrofilmSpecs)
graph.add_node('validate', validate_specs)
graph.add_node('qc', quality_check)
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate')
graph = graph.compile()