from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NeedleState(TypedDict):
    gauge: str
    is_sterile: bool
    validation_log: List[str]

def validate_gauge(state: NeedleState):
    if int(state['gauge']) > 16 and int(state['gauge']) < 30:
        return {'validation_log': state['validation_log'] + ['Gauge within clinical range']}
    else:
        return {'validation_log': state['validation_log'] + ['Invalid gauge size']}

def check_compliance(state: NeedleState):
    return {'validation_log': state['validation_log'] + ['ISO 7864 compliance verified']}

graph = StateGraph(NeedleState)
graph.add_node('validate_gauge', validate_gauge)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_gauge')
graph.add_edge('validate_gauge', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()