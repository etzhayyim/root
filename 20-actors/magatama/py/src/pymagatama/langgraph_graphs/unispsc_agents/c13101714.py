from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiliconProcurementState(TypedDict):
    purity_level: float
    inspection_passed: bool
    log: List[str]

def validate_silicon_purity(state: SiliconProcurementState):
    passed = state['purity_level'] >= 99.999
    return {'inspection_passed': passed, 'log': state['log'] + [f'Purity check: {passed}']}

def route_by_purity(state: SiliconProcurementState):
    return 'validate' if not state.get('inspection_passed') else END

graph = StateGraph(SiliconProcurementState)
graph.add_node('validate', validate_silicon_purity)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
