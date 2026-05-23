from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity_level: float
    safety_check_passed: bool
    history: Annotated[List[str], list.append]

def validate_purity(state: CatalystState) -> CatalystState:
    if state['purity_level'] < 0.99:
        state['history'].append('Purity check failed')
        state['safety_check_passed'] = False
    else:
        state['history'].append('Purity check passed')
        state['safety_check_passed'] = True
    return state

def route_by_safety(state: CatalystState) -> str:
    return 'process' if state['safety_check_passed'] else END

def process_catalyst(state: CatalystState) -> CatalystState:
    state['history'].append('Initiating chemical distribution workflow')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_catalyst)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph = graph.compile()
