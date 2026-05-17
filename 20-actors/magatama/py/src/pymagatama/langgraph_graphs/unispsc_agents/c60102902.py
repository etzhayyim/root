from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    order_id: str
    spec_compliance: bool
    validation_tasks: List[str]

def validate_paper_spec(state: ProcurementState):
    print(f'Validating specs for order {state['order_id']}')
    return {'spec_compliance': True, 'validation_tasks': ['quality_check', 'quantity_verify']}

def approval_step(state: ProcurementState):
    return {'validation_tasks': state['validation_tasks'] + ['approved']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()