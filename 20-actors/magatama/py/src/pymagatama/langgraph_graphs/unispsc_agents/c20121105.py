from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ServoProcState(TypedDict):
    part_number: str
    spec_compliance: bool
    validation_log: Annotated[List[str], operator.add]

def validate_servo_specs(state: ServoProcState):
    log = []
    if state['part_number'].startswith('SM-'):
        state['spec_compliance'] = True
        log.append(f'Validated standard industrial servo: {state['part_number']}')
    else:
        state['spec_compliance'] = False
        log.append(f'Invalid part number format: {state['part_number']}')
    return {'validation_log': log}

def check_safety_protocols(state: ServoProcState):
    log = []
    if state['spec_compliance']:
        log.append('Safety protocols approved for high-torque operation.')
    return {'validation_log': log}

graph = StateGraph(ServoProcState)
graph.add_node('validate', validate_servo_specs)
graph.add_node('safety', check_safety_protocols)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
