from typing import TypedDict
from langgraph.graph import StateGraph, END

class DNAKitState(TypedDict):
    kit_id: str
    purity_check: bool
    yield_check: bool

def validate_purity(state: DNAKitState):
    print(f'Checking DNA purity for kit: {state[\'kit_id\']}')
    return {'purity_check': True}

def validate_yield(state: DNAKitState):
    print(f'Verifying extraction yield for kit: {state[\'kit_id\']}')
    return {'yield_check': True}

graph = StateGraph(DNAKitState)
graph.add_node('purity', validate_purity)
graph.add_node('yield', validate_yield)
graph.set_entry_point('purity')
graph.add_edge('purity', 'yield')
graph.add_edge('yield', END)
compile_graph = graph.compile()