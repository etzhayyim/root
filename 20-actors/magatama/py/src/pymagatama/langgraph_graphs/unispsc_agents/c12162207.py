from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AluminaProcessState(TypedDict):
    material_id: str
    purity_validated: bool
    grain_size_compliance: bool
    hazard_check: bool
    final_approval: bool

def validate_purity(state: AluminaProcessState):
    print(f'Validating purity for {state['material_id']}')
    return {'purity_validated': True}

def check_grain_size(state: AluminaProcessState):
    print('Checking grain size distribution')
    return {'grain_size_compliance': True}

def perform_hazard_review(state: AluminaProcessState):
    print('Performing dual-use hazard review')
    return {'hazard_check': True}

graph = StateGraph(AluminaProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_grain_size', check_grain_size)
graph.add_node('hazard_review', perform_hazard_review)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_grain_size')
graph.add_edge('check_grain_size', 'hazard_review')
graph.add_edge('hazard_review', END)
graph = graph.compile()