from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_compliant: bool
    validation_logs: List[str]

def validate_purity(state: ChemicalState):
    is_pure = state['purity_level'] >= 99.0
    return {'safety_compliant': is_pure, 'validation_logs': ['Purity check passed' if is_pure else 'Purity failed']}

def check_regulatory(state: ChemicalState):
    return {'validation_logs': state['validation_logs'] + ['Regulatory compliance checked']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('regulatory', check_regulatory)
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
