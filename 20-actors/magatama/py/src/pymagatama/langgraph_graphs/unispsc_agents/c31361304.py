from typing import TypedDict
from langgraph.graph import StateGraph, END
class InconelState(TypedDict): n_code: str; spec_data: dict; approved: bool
def validate_welds(state: InconelState): return {'approved': state['spec_data'].get('weld_integrity', False)}
def check_export(state: InconelState): return {'approved': state['spec_data'].get('export_permit', True)}
graph = StateGraph(InconelState)
graph.add_node('validate_welds', validate_welds)
graph.add_node('check_export', check_export)
graph.set_entry_point('validate_welds')
graph.add_edge('validate_welds', 'check_export')
graph.add_edge('check_export', END)
graph = graph.compile()