from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_type: str
    specifications: dict
    validation_passed: bool

def validate_sheathing(state: ProcurementState):
    moisture = state['specifications'].get('moisture_content', 0)
    if moisture < 15:
        return {'validation_passed': True}
    return {'validation_passed': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_sheathing)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
