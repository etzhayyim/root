from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    part_id: str
    specs: dict
    quality_status: bool
    log: List[str]

def validate_specs(state: FastenerState):
    # Perform dimensional and strength validation
    is_valid = state['specs'].get('tensile_strength', 0) >= 800
    return {'quality_status': is_valid, 'log': ['Spec validation complete']}

def perform_inspection(state: FastenerState):
    # Simulate physical inspection
    return {'log': state['log'] + ['Physical inspection verified']}

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
