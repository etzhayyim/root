from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperState(TypedDict):
    specs: dict
    validation_log: list
    is_approved: bool

def validate_purity(state: CopperState):
    purity = state['specs'].get('purity_percentage', 0)
    valid = purity >= 99.9
    return {'validation_log': [f'Purity check: {valid}'], 'is_approved': valid}

def check_dimensions(state: CopperState):
    log = state['validation_log'] + ['Dimension inspection performed']
    return {'validation_log': log}

graph = StateGraph(CopperState)
graph.add_node('purity_check', validate_purity)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'dim_check')
graph.add_edge('dim_check', END)
graph = graph.compile()
