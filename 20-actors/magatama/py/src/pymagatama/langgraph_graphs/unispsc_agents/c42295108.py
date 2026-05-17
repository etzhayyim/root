from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalTableState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_imaging_compatibility(state: SurgicalTableState):
    compatible = state['specs'].get('radiolucent', False)
    log = ['Imaging compatibility verified'] if compatible else ['Imaging compatibility failed']
    return {'is_compliant': compatible, 'validation_log': log}

def check_weight_limit(state: SurgicalTableState):
    cap = state['specs'].get('max_weight', 0)
    passed = cap >= 200
    return {'is_compliant': state['is_compliant'] and passed, 'validation_log': state['validation_log'] + ['Weight capacity checked']}

graph = StateGraph(SurgicalTableState)
graph.add_node('validate_imaging', validate_imaging_compatibility)
graph.add_node('check_weight', check_weight_limit)
graph.set_entry_point('validate_imaging')
graph.add_edge('validate_imaging', 'check_weight')
graph.add_edge('check_weight', END)
graph = graph.compile()