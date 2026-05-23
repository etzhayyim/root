from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    purity_level: float
    storage_temp: float
    is_compliant: bool

def validate_chemistry(state: ReagentState):
    # Business logic for reagent validation
    state['is_compliant'] = state['purity_level'] >= 99.0 and -20 <= state['storage_temp'] <= 8
    return state

graph = StateGraph(ReagentState)
graph.add_node("validate", validate_chemistry)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compile = graph.compile()
