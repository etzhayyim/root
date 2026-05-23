from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ValveState(TypedDict):
    valve_id: str
    spec_data: dict
    validation_log: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_valve_spec(state: ValveState):
    log = []
    compliant = True
    if state['spec_data'].get('pressure_rating_mpa', 0) <= 0:
        log.append('Invalid pressure rating.')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def process_procurement(state: ValveState):
    return {'validation_log': ['Procurement workflow initiated.']}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_valve_spec)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()
