from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BlastingState(TypedDict):
    material_spec: dict
    safety_clearance: bool
    transit_logs: Annotated[Sequence[str], operator.add]

def validate_materials(state: BlastingState):
    spec = state['material_spec']
    is_safe = all(k in spec for k in ['UN_number', 'detonation_velocity'])
    return {'safety_clearance': is_safe}

def process_logistics(state: BlastingState):
    if state['safety_clearance']:
        return {'transit_logs': ['Clearance confirmed', 'Transport protocol activated']}
    return {'transit_logs': ['Clearance failed - halt']}

graph = StateGraph(BlastingState)
graph.add_node('validate', validate_materials)
graph.add_node('logistics', process_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
