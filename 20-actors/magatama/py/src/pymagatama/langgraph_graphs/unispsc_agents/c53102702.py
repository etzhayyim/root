from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class UniformState(TypedDict):
    order_id: str
    specs: dict
    is_compliant: bool
    history: List[str]

def validate_specs(state: UniformState):
    # Business logic for textile compliance check
    required = ['material', 'durability_grade']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance}

def finalize_order(state: UniformState):
    return {'history': state['history'] + ['Order Finalized']}

graph = StateGraph(UniformState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
