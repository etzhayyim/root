from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IceMakerState(TypedDict):
    capacity_kg: float
    refrigerant: str
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: IceMakerState):
    log = []
    compliant = True
    if state['capacity_kg'] < 100:
        log.append('Low capacity warning')
    if state['refrigerant'] not in ['R290', 'R404A']:
        log.append('Non-standard refrigerant')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(IceMakerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()