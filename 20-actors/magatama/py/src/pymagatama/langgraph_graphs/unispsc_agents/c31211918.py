from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MaskState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: MaskState):
    solvent_res = state['spec_data'].get('solvent_resistance', False)
    return {'validation_passed': solvent_res, 'errors': [] if solvent_res else ['Incompatible materials']}

def check_dimensions(state: MaskState):
    return {'validation_passed': True}

graph = StateGraph(MaskState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_dimensions')
graph.add_edge('check_dimensions', END)
app = graph.compile()