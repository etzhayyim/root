from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class PaperProcurementState(TypedDict):
    material_specs: dict
    validation_logs: Annotated[list[str], operator.add]
    is_approved: bool

def validate_industrial_paper(state: PaperProcurementState):
    specs = state['material_specs']
    logs = []
    if specs.get('basis_weight_gsm', 0) < 50:
        logs.append('Insufficient basis weight for industrial application')
    return {'validation_logs': logs}

def quality_control_check(state: PaperProcurementState):
    is_valid = len(state['validation_logs']) == 0
    return {'is_approved': is_valid}

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_industrial_paper)
graph.add_node('qc', quality_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()