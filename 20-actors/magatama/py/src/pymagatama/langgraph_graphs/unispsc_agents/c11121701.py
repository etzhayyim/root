from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
import operator

class MineralState(TypedDict):
    commodity_id: str
    raw_data: dict
    validation_results: Annotated[List[str], operator.add]
    is_approved: bool

def validate_purity(state: MineralState):
    purity = state['raw_data'].get('purity', 0)
    if purity >= 95.0:
        return {'validation_results': ['Purity check passed'], 'is_approved': True}
    return {'validation_results': ['Purity check failed'], 'is_approved': False}

def process_logistics(state: MineralState):
    return {'validation_results': ['Logistics verification complete']}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('logistics', process_logistics)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
