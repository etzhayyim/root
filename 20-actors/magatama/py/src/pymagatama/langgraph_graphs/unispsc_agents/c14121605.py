from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class TapeProcurementState(TypedDict):
    commodity_code: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_tape_specs(state: TapeProcurementState):
    specs = state['specs']
    log = []
    compliant = True
    if specs.get('thickness_microns', 0) < 30:
        log.append('Thickness below industrial standard.')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

def process_procurement(state: TapeProcurementState):
    print('Processing high-performance tape order...')
    return {'validation_log': ['Order processed for logistics']}

graph = StateGraph(TapeProcurementState)
graph.add_node('validate', validate_tape_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()