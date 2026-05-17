from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class OfficePaperState(TypedDict):
    requisition_id: str
    spec_requirements: dict
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_paper_specs(state: OfficePaperState):
    specs = state['spec_requirements']
    logs = []
    if specs.get('basis_weight', 0) < 60:
        logs.append('Insufficient basis weight for standard use.')
    return {'validation_log': logs, 'status': 'validated' if not logs else 'rejected'}

def update_inventory_status(state: OfficePaperState):
    return {'status': 'inventory_updated'}

graph = StateGraph(OfficePaperState)
graph.add_node('validate', validate_paper_specs)
graph.add_node('update', update_inventory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph = graph.compile()