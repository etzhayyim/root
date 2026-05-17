from langgraph.graph import StateGraph, END
from typing import TypedDict
class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    has_sds: bool
    is_compliant: bool
def validate_chemical(state: ChemicalState):
    state['is_compliant'] = state['has_sds'] and state['purity'] >= 98.0
    return state
graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemical)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()