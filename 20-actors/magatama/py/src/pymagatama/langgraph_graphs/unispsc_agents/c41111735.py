from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroscopeGraphState(TypedDict):
    stage_specs: dict
    validation_log: list
    is_compliant: bool

def validate_precision(state: MicroscopeGraphState):
    accuracy = state['stage_specs'].get('accuracy', 1.0)
    valid = accuracy <= 0.5
    return {'validation_log': [f"Precision check: {'Pass' if valid else 'Fail'}"], 'is_compliant': valid}

def check_dual_use(state: MicroscopeGraphState):
    return {'validation_log': state['validation_log'] + ['Export control check: Flagged for high-precision optics']}

graph = StateGraph(MicroscopeGraphState)
graph.add_node("precision_check", validate_precision)
graph.add_node("export_check", check_dual_use)
graph.set_entry_point("precision_check")
graph.add_edge("precision_check", "export_check")
graph.add_edge("export_check", END)
app = graph.compile()