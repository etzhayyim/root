from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    product_name: str
    quality_docs: List[str]
    is_compliant: bool

def validate_quality(state: FoodSupplyState):
    # Business logic for nuts and seeds inspection
    state['is_compliant'] = 'pesticide_report' in state['quality_docs']
    return state

def finalize_procurement(state: FoodSupplyState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(FoodSupplyState)
graph.add_node('validate', validate_quality)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
