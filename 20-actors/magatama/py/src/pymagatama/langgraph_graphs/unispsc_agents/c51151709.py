from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    purity: float
    has_gmp: bool
    compliance_check: bool

def validate_purity(state: State) -> State:
    state['compliance_check'] = state['purity'] >= 99.0 and state['has_gmp']
    return state

def check_regulatory(state: State) -> State:
    if not state['compliance_check']:
        print('Regulatory compliance failed.')
    return state

graph = StateGraph(State)
graph.add_node('validate', validate_purity)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
