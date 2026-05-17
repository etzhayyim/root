from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
import operator

class MineralState(TypedDict):
    commodity_code: str
    purity_check: bool
    lab_results: dict
    inspection_status: str
    log: Annotated[List[str], operator.add]

def validate_purity(state: MineralState):
    purity = state['lab_results'].get('purity', 0)
    is_valid = purity >= 95.0
    return {'purity_check': is_valid, 'inspection_status': 'passed' if is_valid else 'rejected', 'log': ['Purity validation completed']}

def route_by_purity(state: MineralState):
    return 'check_composition' if state['purity_check'] else END

def check_composition(state: MineralState):
    return {'inspection_status': 'verified', 'log': ['Chemical composition analysis completed']}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_composition', check_composition)
graph.set_entry_point('validate_purity')
graph.add_conditional_edges('validate_purity', route_by_purity)
graph.add_edge('check_composition', END)
graph = graph.compile()