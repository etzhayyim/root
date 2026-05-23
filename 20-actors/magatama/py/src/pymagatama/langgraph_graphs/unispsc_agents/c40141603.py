from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: ValveState):
    log = []
    compliant = True
    required = ['MaxPressure', 'PortSize']
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing {field}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def route_by_compliance(state: ValveState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(ValveState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'validation_log': ['Approved for procurement']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
