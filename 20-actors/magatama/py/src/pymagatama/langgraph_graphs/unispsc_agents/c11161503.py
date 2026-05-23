from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SiCState(TypedDict):
    purity: float
    particle_size: float
    export_cleared: bool
    validation_log: List[str]

def validate_purity(state: SiCState) -> dict:
    purity = state.get('purity', 0)
    if purity >= 99.9:
        return {'validation_log': state['validation_log'] + ['Purity verified: High Grade']}
    return {'validation_log': state['validation_log'] + ['Purity below threshold']}

def check_export_control(state: SiCState) -> dict:
    if state.get('export_cleared'):
        return {'validation_log': state['validation_log'] + ['Export control cleared']}
    return {'validation_log': state['validation_log'] + ['Export control required']}

graph = StateGraph(SiCState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_export_control', check_export_control)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_export_control')
graph.add_edge('check_export_control', END)
compile = graph.compile()
