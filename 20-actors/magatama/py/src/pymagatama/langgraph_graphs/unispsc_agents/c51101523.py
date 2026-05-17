from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    purity_check: bool
    safety_validation: bool
    log: List[str]

def validate_purity(state: ReagentState) -> ReagentState:
    # Simulate chemical purity validation logic
    state['purity_check'] = True
    state['log'].append('Purity verified against specification.')
    return state

def validate_safety(state: ReagentState) -> ReagentState:
    # Simulate SDS and hazardous material compliance
    state['safety_validation'] = True
    state['log'].append('Safety protocols and SDS verified.')
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('validate_safety', validate_safety)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'validate_safety')
graph.add_edge('validate_safety', END)
compile_graph = graph.compile()