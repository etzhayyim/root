from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity: float
    status: str
    safety_check: bool

def validate_purity(state: ChemicalState):
    return {'status': 'VALIDATED' if state['purity'] >= 0.99 else 'REJECTED'}

def safety_protocol(state: ChemicalState):
    return {'safety_check': state['status'] == 'VALIDATED'}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_protocol)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
