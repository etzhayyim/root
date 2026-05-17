from typing import TypedDict, List, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MiningPartState(TypedDict):
    part_id: str
    spec_requirements: dict
    inspection_results: List[str]
    validation_log: Annotated[List[str], operator.add]

def validate_material_specs(state: MiningPartState):
    log = [f'Validating material specs for {state[\'part_id\']}']
    return {'validation_log': log}

def perform_dimensional_check(state: MiningPartState):
    log = [f'Performing dimensional tolerance check for {state[\'part_id\']}']
    return {'validation_log': log}

graph = StateGraph(MiningPartState)
graph.add_node('validate', validate_material_specs)
graph.add_node('check', perform_dimensional_check)
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()