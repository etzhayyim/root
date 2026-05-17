from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BreedingState(TypedDict):
    material_id: str
    sanitary_clearance: bool
    pedigree_verified: bool
    final_status: str

def check_sanitary(state: BreedingState):
    print(f'Checking sanitary permit for {state[material_id]}')
    return {sanitary_clearance: True}

def verify_pedigree(state: BreedingState):
    print(f'Verifying pedigree data for {state[material_id]}')
    return {pedigree_verified: True}

def finalize_ingest(state: BreedingState):
    return {final_status: READY_FOR_STORAGE}

graph = StateGraph(BreedingState)
graph.add_node(sanitary_check, check_sanitary)
graph.add_node(pedigree_check, verify_pedigree)
graph.add_node(finalizer, finalize_ingest)
graph.set_entry_point(sanitary_check)
graph.add_edge(sanitary_check, pedigree_check)
graph.add_edge(pedigree_check, finalizer)
graph.add_edge(finalizer, END)
compiled_graph = graph.compile()