from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ButtonState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_material(state: ButtonState):
    material = state['spec_data'].get('material', 'none')
    is_valid = material in ['brass', 'stainless_steel', 'zinc_alloy']
    return {'validation_log': [f'Material check: {material} -> {is_valid}'], 'is_approved': is_valid}

def final_check(state: ButtonState):
    status = 'Approved' if state['is_approved'] else 'Rejected'
    return {'validation_log': [f'Final status: {status}']}

graph = StateGraph(ButtonState)
graph.add_node('material_check', validate_material)
graph.add_node('final', final_check)
graph.add_edge('material_check', 'final')
graph.add_edge('final', END)
graph.set_entry_point('material_check')
graph = graph.compile()