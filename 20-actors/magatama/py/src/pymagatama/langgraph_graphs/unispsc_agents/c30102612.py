from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ZincState(TypedDict):
    purity: float
    dimensions: dict
    compliant: bool
    log: List[str]

def validate_purity(state: ZincState):
    is_pure = state['purity'] >= 99.9
    return {'compliant': is_pure, 'log': [f'Purity check: {is_pure}の結果']}

def structural_check(state: ZincState):
    valid_dim = all(val > 0 for val in state['dimensions'].values())
    return {'compliant': state['compliant'] and valid_dim, 'log': ['構造寸法検査完了']}

graph = StateGraph(ZincState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('structural_check', structural_check)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'structural_check')
graph.add_edge('structural_check', END)

compiled_graph = graph.compile()
