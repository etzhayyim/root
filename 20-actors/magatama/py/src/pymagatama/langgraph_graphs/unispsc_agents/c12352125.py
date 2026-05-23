from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ChemicalProcurementState(TypedDict):
    material_id: str
    purity: float
    safety_clearance: bool
    history: Annotated[list, operator.add]

def validate_composition(state: ChemicalProcurementState):
    # Simulate composition validation against safety protocols
    is_safe = state['purity'] >= 0.99
    return {'safety_clearance': is_safe, 'history': ['Validated composition']}

def route_procurement(state: ChemicalProcurementState):
    if state['safety_clearance']:
        return 'process_order'
    return 'flag_for_review'

def process_order(state: ChemicalProcurementState):
    return {'history': ['Order processing initialized']}

def flag_for_review(state: ChemicalProcurementState):
    return {'history': ['Flagged for secondary safety audit']}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_composition)
graph.add_node('process_order', process_order)
graph.add_node('flag_for_review', flag_for_review)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('process_order', END)
graph.add_edge('flag_for_review', END)
graph = graph.compile()
