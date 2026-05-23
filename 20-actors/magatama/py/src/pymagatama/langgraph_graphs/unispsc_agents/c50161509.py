from typing import TypedDict
from langgraph.graph import StateGraph, END

class SugarState(TypedDict):
    purity: float
    brix: float
    is_compliant: bool

def validate_sugar_specs(state: SugarState):
    compliant = state['purity'] >= 99.0 and 60 <= state['brix'] <= 75
    return {'is_compliant': compliant}

graph = StateGraph(SugarState)
graph.add_node('validate', validate_sugar_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
