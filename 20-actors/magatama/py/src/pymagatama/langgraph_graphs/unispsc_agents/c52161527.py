from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_audio_specs(state: AuditState):
    specs = state['specs']
    logs = []
    if specs.get('rms_power_output_watts', 0) <= 0:
        logs.append('Invalid power rating')
    return {'validation_log': logs, 'approved': len(logs) == 0}

def finalize_procurement(state: AuditState):
    return {'approved': True}

graph = StateGraph(AuditState)
graph.add_node('validate', validate_audio_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph.compile()
