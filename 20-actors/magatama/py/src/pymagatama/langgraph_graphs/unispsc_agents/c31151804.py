from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StapleWireSpec(TypedDict):
    gauge: float
    tensile_strength: float
    is_compliant: bool
    validation_log: List[str]

def validate_wire_specs(state: StapleWireSpec):
    log = []
    if state['gauge'] <= 0:
        log.append('Invalid gauge size.')
    if state['tensile_strength'] < 500:
        log.append('Low tensile strength.')
    return {'is_compliant': len(log) == 0, 'validation_log': log}

graph = StateGraph(StapleWireSpec)
graph.add_node('validate', validate_wire_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()