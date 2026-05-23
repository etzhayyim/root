from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PrecisionPartState(TypedDict):
    part_id: str
    spec_requirements: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_dimensions(state: PrecisionPartState):
    log = f'Validating dimensions for {state.part_id}'
    return {'validation_log': [log], 'is_approved': True}

def check_material(state: PrecisionPartState):
    log = f'Verifying material grade for {state.part_id}'
    return {'validation_log': [log]}

graph = StateGraph(PrecisionPartState)
graph.add_node('validate', validate_dimensions)
graph.add_node('material', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material')
graph.add_edge('material', END)
compile_graph = graph.compile()
