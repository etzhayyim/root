from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class InfantApparelState(TypedDict):
    material_certified: bool
    safety_tests_passed: bool
    log: List[str]

def check_compliance(state: InfantApparelState):
    is_safe = state.get('material_certified') and state.get('safety_tests_passed')
    state['log'].append(f'Compliance status: {is_safe}')
    return 'safe' if is_safe else 'reject'

graph = StateGraph(InfantApparelState)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
