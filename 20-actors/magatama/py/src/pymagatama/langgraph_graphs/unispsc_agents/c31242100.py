from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OpticalState(TypedDict):
    part_number: str
    specs: dict
    valid: bool
    export_control_flag: bool

def validate_specs(state: OpticalState):
    state['valid'] = 'tolerance' in state['specs'] and 'material' in state['specs']
    return state

def check_export(state: OpticalState):
    restricted_keywords = ['laser', 'thermal', 'military']
    state['export_control_flag'] = any(k in str(state['specs']).lower() for k in restricted_keywords)
    return state

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
