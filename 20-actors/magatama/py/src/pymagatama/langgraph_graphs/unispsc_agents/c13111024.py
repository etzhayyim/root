from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    chemical_id: str
    purity_validated: bool
    safety_clearance: bool
    logistics_approved: bool
    messages: Annotated[Sequence[str], operator.add]

def validate_purity(state: ChemicalState) -> ChemicalState:
    # Simulate purity analysis
    state['purity_validated'] = True
    state['messages'] = ['Purity validation passed for ' + state['chemical_id']]
    return state

def check_safety(state: ChemicalState) -> ChemicalState:
    # Simulate safety compliance check
    state['safety_clearance'] = True
    state['messages'] = ['Safety clearance obtained']
    return state

def approve_logistics(state: ChemicalState) -> ChemicalState:
    # Simulate logistics approval
    state['logistics_approved'] = True
    state['messages'] = ['Logistics chain verified']
    return state

graph = StateGraph(ChemicalState)
graph.add_node('purity', validate_purity)
graph.add_node('safety', check_safety)
graph.add_node('logistics', approve_logistics)
graph.set_entry_point('purity')
graph.add_edge('purity', 'safety')
graph.add_edge('safety', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
