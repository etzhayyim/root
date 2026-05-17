from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    item_id: str
    quantity: int
    specs: dict
    validation_errors: List[str]
    status: str

def validate_specs(state: PaperProcurementState):
    errors = []
    if 'paper_weight_gsm' not in state['specs']:
        errors.append('Missing paper weight specification')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'rejected'}

def route_procurement(state: PaperProcurementState):
    return 'process_order' if state['status'] == 'validated' else END

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', lambda s: {'status': 'processed'})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('process_order', END)
graph = graph.compile()