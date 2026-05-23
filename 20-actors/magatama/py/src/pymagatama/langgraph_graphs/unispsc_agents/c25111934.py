from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TillerProcurementState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: TillerProcurementState):
    specs = state['specs']
    logs = []
    compliant = True
    if specs.get('power', 0) < 5:
        logs.append('Insufficient engine power')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': logs}

def route_procurement(state: TillerProcurementState):
    return 'compliant' if state['is_compliant'] else END

graph = StateGraph(TillerProcurementState)
graph.add_node('validator', validate_specs)
graph.add_edge('validator', END)
graph.set_entry_point('validator')
graph = graph.compile()
