from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrassItemState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_alloy_specs(state: BrassItemState):
    alloy = state['specs'].get('alloy_type')
    if alloy in ['C360', 'C260']:
        return {'validation_passed': True}
    return {'validation_passed': False, 'error_log': ['Invalid alloy specification']}

def check_dimensions(state: BrassItemState):
    dim = state['specs'].get('dimensions', {})
    if all(k in dim for k in ['length', 'width', 'thickness']):
        return {'validation_passed': True}
    return {'validation_passed': False, 'error_log': ['Missing dimension parameters']}

graph = StateGraph(BrassItemState)
graph.add_node('validate_alloy', validate_alloy_specs)
graph.add_node('check_dims', check_dimensions)
graph.add_edge('validate_alloy', 'check_dims')
graph.add_edge('check_dims', END)
graph.set_entry_point('validate_alloy')
graph = graph.compile()