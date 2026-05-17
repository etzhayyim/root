from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class ChemicalProcessState(TypedDict):
    batch_id: str
    purity_level: float
    safety_check_passed: bool
    process_logs: List[str]

def validate_purity(state: ChemicalProcessState) -> ChemicalProcessState:
    if state['purity_level'] < 99.9:
        state['process_logs'].append('Purity check failed')
        state['safety_check_passed'] = False
    else:
        state['process_logs'].append('Purity verified')
    return state

def logistics_handler(state: ChemicalProcessState) -> ChemicalProcessState:
    if state['safety_check_passed']:
        state['process_logs'].append('Logistics approved for hazardous materials')
    return state

graph = StateGraph(ChemicalProcessState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('logistics_handler', logistics_handler)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'logistics_handler')
graph.add_edge('logistics_handler', END)

compiled_graph = graph.compile()