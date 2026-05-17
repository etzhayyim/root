from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LiquidNitrogenState(TypedDict):
    purity_level: float
    container_pressure: float
    safety_clearance: bool
    log_entries: Annotated[Sequence[str], operator.add]

def validate_purity(state: LiquidNitrogenState):
    if state['purity_level'] < 99.999:
        return {'log_entries': ['Purity level insufficient for semiconductor grade']}
    return {'safety_clearance': True, 'log_entries': ['Purity verified']}

def check_container(state: LiquidNitrogenState):
    if state['container_pressure'] > 5.0:
        return {'safety_clearance': False, 'log_entries': ['High pressure alert - storage rejected']}
    return {'log_entries': ['Container integrity checked']}

def process_delivery(state: LiquidNitrogenState):
    if state.get('safety_clearance'):
        return {'log_entries': ['Delivery scheduled', 'Cryogenic handling protocol activated']}
    return {'log_entries': ['Delivery aborted']}

graph = StateGraph(LiquidNitrogenState)
graph.add_node('validate', validate_purity)
graph.add_node('inspect', check_container)
graph.add_node('dispatch', process_delivery)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', 'dispatch')
graph.add_edge('dispatch', END)
graph = graph.compile()