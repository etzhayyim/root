from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ChemicalState(TypedDict):
    batch_id: str
    purity_check: bool
    is_compliant: bool
    hazard_level: int

def validate_purity(state: ChemicalState):
    # Simulate purity verification
    state['purity_check'] = True
    return state

def check_compliance(state: ChemicalState):
    # Validate against export/safety regulations
    state['is_compliant'] = state['hazard_level'] < 5
    return state

graph = StateGraph(ChemicalState)
graph.add_node('purity', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('purity')
graph.add_edge('purity', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
