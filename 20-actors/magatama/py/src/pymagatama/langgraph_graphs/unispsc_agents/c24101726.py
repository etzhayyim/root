from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class LinerProcurementState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: Annotated[list, operator.add]

def validate_material(state: LinerProcurementState):
    material = state['spec_data'].get('material', '')
    is_valid = len(material) > 0
    return {'validation_result': is_valid, 'error_log': ['Invalid material' if not is_valid else 'Material OK']}

def check_durability(state: LinerProcurementState):
    hardness = state['spec_data'].get('shore_hardness', 0)
    return {'validation_result': hardness > 50}

graph = StateGraph(LinerProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_durability', check_durability)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_durability')
graph.add_edge('check_durability', END)
app = graph.compile()