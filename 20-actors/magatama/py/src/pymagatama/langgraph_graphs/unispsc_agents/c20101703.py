from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    pressure_req: float
    stroke_len: float
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: HydraulicState):
    log = []
    if state['pressure_req'] > 70.0:
        log.append('High pressure requirement detected, requires reinforced seals.')
    if state['stroke_len'] <= 0:
        raise ValueError('Invalid stroke length')
    return {'validation_log': log, 'is_compliant': True}

def process_procurement(state: HydraulicState):
    return {'validation_log': ['Procurement order drafted for hydraulic actuator.']}

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_specs)
graph.add_node('procure', process_procurement)
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph.set_entry_point('validate')
graph = graph.compile()