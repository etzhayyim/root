from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    paper_specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: PaperProcurementState):
    specs = state['paper_specs']
    logs = []
    compliant = True
    if not specs.get('acid_free_certification'):
        logs.append('Warning: Missing acid-free certification')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def archival_check(state: PaperProcurementState):
    if state['paper_specs'].get('archival_longevity_rating', 0) < 100:
        return {'validation_logs': ['Insufficient archival rating for long-term storage']}
    return {'validation_logs': ['Archival standards met']}

workflow = StateGraph(PaperProcurementState)
workflow.add_node('validate', validate_specs)
workflow.add_node('archive', archival_check)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'archive')
workflow.add_edge('archive', END)
graph = workflow.compile()
