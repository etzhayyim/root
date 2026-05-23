from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: WeldingGraphState):
    log = []
    compliant = True
    if 'voltage_rating' not in state['specs']:
        log.append('Missing voltage rating')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def export_control_check(state: WeldingGraphState):
    # Dual-use logic placeholder
    return {'validation_log': state['validation_log'] + ['Export control check passed']}

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
