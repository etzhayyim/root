from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    specs: dict
    validation_passed: bool
    is_dual_use: bool

def validate_specs(state: WeldingGraphState):
    state['validation_passed'] = all(k in state['specs'] for k in ['power', 'material_type'])
    return state

def check_export_control(state: WeldingGraphState):
    state['is_dual_use'] = state['specs'].get('precision_level') == 'high'
    return state

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
compile = graph.compile()
