from typing import TypedDict
from langgraph.graph import StateGraph, END
class ChartingState(TypedDict):
    data_payload: dict
    validation_errors: list
    is_compliant: bool
def validate_data_format(state: ChartingState):
    errors = []
    if not state['data_payload'].get('format'):
        errors.append('Missing mandatory data format')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}
def check_licensing(state: ChartingState):
    return {'is_compliant': state['is_compliant'] and 'license' in state['data_payload']}
graph = StateGraph(ChartingState)
graph.add_node('format_check', validate_data_format)
graph.add_node('license_check', check_licensing)
graph.set_entry_point('format_check')
graph.add_edge('format_check', 'license_check')
graph.add_edge('license_check', END)
graph = graph.compile()
