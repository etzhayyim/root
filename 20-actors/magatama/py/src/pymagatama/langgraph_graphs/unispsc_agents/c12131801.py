from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ResinState(TypedDict):
    batch_id: str
    purity_metrics: dict
    workflow_status: List[str]

def validate_purity(state: ResinState):
    print(f'Validating purity for {state['batch_id']}')
    return {'workflow_status': ['Purity Validated']}

def process_resin(state: ResinState):
    print('Executing polymerization workflow')
    return {'workflow_status': ['Workflow Complete']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_resin)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()