from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireState(TypedDict):
    specs: dict
    approved: bool

def validate_insulation(state: WireState):
    if state['specs'].get('insulation_type') in ['PVC', 'XLPE', 'LSZH']:
        return {'approved': True}
    return {'approved': False}

def check_compliance(state: WireState):
    if state['approved'] and 'UL' in state['specs'].get('standard', ''):
        return 'final'
    return 'final'

graph = StateGraph(WireState)
graph.add_node('validation', validate_insulation)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validation')
graph.add_edge('validation', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()