from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    purity_level: float
    status: str
    history: Annotated[Sequence[str], operator.add]

def validate_purity(state: ReagentState):
    is_pure = state['purity_level'] >= 0.99
    return {'status': 'validated' if is_pure else 'rejected', 'history': ['Purity check completed']}

def check_storage(state: ReagentState):
    return {'status': 'approved', 'history': ['Storage conditions verified']}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_purity)
graph.add_node('storage', check_storage)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph = graph.compile()