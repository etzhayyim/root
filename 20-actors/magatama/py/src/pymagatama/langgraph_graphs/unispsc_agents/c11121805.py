from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class KOHState(TypedDict):
    purity_requirement: float
    batch_id: str
    validation_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: KOHState):
    passed = state['purity_requirement'] >= 99.0
    return {'validation_passed': passed, 'log': [f'Purity check: {passed}']}

def chemical_workflow(state: KOHState):
    if state['validation_passed']:
        return 'ready_for_dispatch'
    return 'flag_for_review'

graph = StateGraph(KOHState)
graph.add_node('validate', validate_purity)
graph.add_node('process', chemical_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

app = graph.compile()
