from typing import TypedDict
from langgraph.graph import StateGraph, END

class MirrorState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: MirrorState):
    required = ['reflectance', 'material']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing specs'}

def check_export_control(state: MirrorState):
    if state['specs'].get('precision', 0) > 0.5:
        print('Dual-use review triggered')
    return {}

graph = StateGraph(MirrorState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
