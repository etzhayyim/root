from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
import operator

class ActuatorState(TypedDict):
    part_number: str
    torque_nm: float
    voltage_v: float
    validation_log: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_actuator_specs(state: ActuatorState):
    log = []
    if state['torque_nm'] <= 0:
        log.append('Invalid torque: must be positive')
    if state['voltage_v'] < 12 or state['voltage_v'] > 48:
        log.append('Voltage outside industrial standard range 12-48V')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def process_procurement(state: ActuatorState):
    print(f'Processing procurement for {state['part_number']}')
    return state

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_actuator_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()