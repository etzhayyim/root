from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity: float
    composition_data: dict
    validation_log: List[str]
    approved: bool

def validate_catalyst_purity(state: CatalystState):
    purity = state.get('purity', 0.0)
    if purity >= 99.99:
        return {'validation_log': state['validation_log'] + ['Purity threshold met'], 'approved': True}
    return {'validation_log': state['validation_log'] + ['Purity insufficient'], 'approved': False}

def process_composition(state: CatalystState):
    return {'validation_log': state['validation_log'] + ['Composition specs analyzed']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_catalyst_purity)
graph.add_node('process', process_composition)
graph.set_entry_point('process')
graph.add_edge('process', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()