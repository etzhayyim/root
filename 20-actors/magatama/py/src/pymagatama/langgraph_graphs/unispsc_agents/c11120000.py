from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ChemicalState(TypedDict):
    chemical_id: str
    purity: float
    safety_score: float
    validated: bool

def validate_purity(state: ChemicalState) -> ChemicalState:
    state['validated'] = state['purity'] >= 99.5
    return state

def assess_safety(state: ChemicalState) -> ChemicalState:
    state['safety_score'] = 1.0 if state['validated'] else 0.0
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', assess_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
compiled_graph = graph.compile()