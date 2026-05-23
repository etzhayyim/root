from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MountState(TypedDict):
    mount_specs: dict
    validation_results: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_specs(state: MountState):
    specs = state['mount_specs']
    errors = []
    if specs.get('adjustment_precision_arcsec', 0) > 60:
        errors.append('Precision requirement not met')
    return {'validation_results': errors, 'is_compliant': len(errors) == 0}

def export_control_check(state: MountState):
    return {'validation_results': ['Export control cleared for non-military end use']}

graph = StateGraph(MountState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
app = graph.compile()
