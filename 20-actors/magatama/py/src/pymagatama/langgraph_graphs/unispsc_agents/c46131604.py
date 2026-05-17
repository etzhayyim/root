from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BoosterState(TypedDict):
    pressure_specs: dict
    compliance_passed: bool
    validation_log: List[str]

def validate_pressure_specs(state: BoosterState):
    log = state.get('validation_log', [])
    if state['pressure_specs'].get('psi', 0) > 5000:
        log.append('High pressure validation triggered')
    return {'validation_log': log, 'compliance_passed': True}

def finalize_order(state: BoosterState):
    return {'validation_log': state['validation_log'] + ['Order finalized']}

graph = StateGraph(BoosterState)
graph.add_node('validate', validate_pressure_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()