from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CutbackState(TypedDict):
    product_specs: dict
    validation_passed: bool
    safety_check_logs: List[str]

def validate_flash_point(state: CutbackState):
    flash_point = state['product_specs'].get('flash_point', 0)
    if flash_point < 38:
        state['safety_check_logs'].append('Critical: Flash point below regulated safe threshold.')
        state['validation_passed'] = False
    return state

def check_voc_compliance(state: CutbackState):
    if 'voc_level' not in state['product_specs']:
        state['safety_check_logs'].append('Missing VOC compliance certificate.')
        state['validation_passed'] = False
    return state

graph = StateGraph(CutbackState)
graph.add_node('validate_flash', validate_flash_point)
graph.add_node('check_voc', check_voc_compliance)
graph.set_entry_point('validate_flash')
graph.add_edge('validate_flash', 'check_voc')
graph.add_edge('check_voc', END)
graph = graph.compile()