from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RareEarthState(TypedDict):
    purity_level: float
    impurity_report: dict
    compliance_flag: bool
    history: Annotated[Sequence[str], operator.add]

def validate_purity(state: RareEarthState):
    is_compliant = state['purity_level'] >= 99.9
    return {'compliance_flag': is_compliant, 'history': ['Validated purity level']}

def check_impurities(state: RareEarthState):
    # Simulate impurity threshold check
    return {'history': ['Performed trace element analysis']}

graph = StateGraph(RareEarthState)
graph.add_node('validate', validate_purity)
graph.add_node('check', check_impurities)
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()