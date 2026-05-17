from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    equipment_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_casting_specs(state: CastingState):
    log = []
    compliant = True
    if 'tolerance' not in state['specs']:
        log.append('Missing tolerance specification')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def process_casting_order(state: CastingState):
    return {'validation_log': ['Order processed for casting equipment']}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_casting_specs)
graph.add_node('process', process_casting_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

graph = graph.compile()