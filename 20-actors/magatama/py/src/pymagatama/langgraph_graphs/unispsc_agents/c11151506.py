from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    batch_id: str
    purity_level: float
    validation_logs: Annotated[Sequence[str], operator.add]
    is_cleared: bool

def validate_purity(state: ChemicalState):
    if state['purity_level'] >= 99.9:
        return {'validation_logs': ['Purity check passed'], 'is_cleared': True}
    return {'validation_logs': ['Purity check failed'], 'is_cleared': False}

def process_sintering(state: ChemicalState):
    if state['is_cleared']:
        return {'validation_logs': ['Sintering parameters configured']}
    return {'validation_logs': ['Skipped sintering: purity insufficient']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('sinter', process_sintering)
graph.add_edge('validate', 'sinter')
graph.add_edge('sinter', END)
graph.set_entry_point('validate')
app = graph.compile()
