from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralChemicalState(TypedDict):
    batch_id: str
    purity: float
    safety_score: float
    approved: bool

def validate_purity(state: MineralChemicalState) -> MineralChemicalState:
    if state['purity'] >= 99.5:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

def safety_check(state: MineralChemicalState) -> MineralChemicalState:
    if state['approved']:
        state['safety_score'] = 1.0
    else:
        state['safety_score'] = 0.0
    return state

graph = StateGraph(MineralChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

compiled_graph = graph.compile()
