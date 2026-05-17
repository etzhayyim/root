from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    mineral_id: str
    purity_level: float
    inspection_passed: bool
    history_log: List[str]

def validate_purity(state: MineralState):
    passed = state['purity_level'] > 0.98
    return {'inspection_passed': passed, 'history_log': state['history_log'] + ['Purity validation completed']}

def update_registry(state: MineralState):
    if state['inspection_passed']:
        return {'history_log': state['history_log'] + ['Logged into central supply registry']}
    return {'history_log': state['history_log'] + ['Failed validation - flagged']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('registry', update_registry)
graph.add_edge('validate', 'registry')
graph.set_entry_point('validate')
graph.add_edge('registry', END)
graph = graph.compile()