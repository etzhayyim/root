from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
import operator

class DrawingConsumableState(TypedDict):
    spec_id: str
    viscosity: float
    compatibility: List[str]
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_ink_specs(state: DrawingConsumableState):
    log = []
    if state['viscosity'] < 1.0 or state['viscosity'] > 50.0:
        log.append(f'Invalid viscosity: {state["viscosity"]} cp')
    return {'validation_log': log}

def check_compatibility(state: DrawingConsumableState):
    if 'polyester' in state['compatibility']:
        return {'validation_log': ['Compatible with polyester film'], 'is_approved': True}
    return {'validation_log': ['Incompatible substrate'], 'is_approved': False}

graph = StateGraph(DrawingConsumableState)
graph.add_node('validate', validate_ink_specs)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()
