from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AdhesionState(TypedDict):
    material_id: str
    viscosity: float
    curing_required: bool
    safety_clearance: bool

def validate_material(state: AdhesionState):
    state['safety_clearance'] = state['viscosity'] > 0 and state['viscosity'] < 50000
    return {'safety_clearance': state['safety_clearance']}

def prepare_application(state: AdhesionState):
    if state['safety_clearance']:
        print(f'Preparing adhesive {state["material_id"]} for application')
    return {'curing_required': True}

graph = StateGraph(AdhesionState)
graph.add_node('validate', validate_material)
graph.add_node('prepare', prepare_application)
graph.add_edge('validate', 'prepare')
graph.add_edge('prepare', END)
graph.set_entry_point('validate')
graph = graph.compile()
