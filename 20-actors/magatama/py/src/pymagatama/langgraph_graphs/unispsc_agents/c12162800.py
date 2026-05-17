from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity: float
    safety_check_passed: bool
    log: List[str]

def validate_purity(state: ChemicalState):
    if state['purity'] >= 99.9:
        state['safety_check_passed'] = True
        state['log'].append('Purity validated for industrial grade.')
    else:
        state['safety_check_passed'] = False
        state['log'].append('Purity failed inspection.')
    return state

def route_by_safety(state: ChemicalState):
    return 'process' if state['safety_check_passed'] else 'reject'

def process_chemical(state: ChemicalState):
    state['log'].append('Chemical processing in controlled environment.')
    return state

def reject_chemical(state: ChemicalState):
    state['log'].append('Chemical rejected due to safety failure.')
    return state

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_chemical)
graph.add_node('reject', reject_chemical)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()