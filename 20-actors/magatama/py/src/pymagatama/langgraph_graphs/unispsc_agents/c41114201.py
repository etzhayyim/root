from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TapeSpecState(TypedDict):
    length_m: float
    precision_class: str
    is_compliant: bool

def validate_tape_specs(state: TapeSpecState):
    state['is_compliant'] = state['length_m'] > 0 and state['precision_class'] in ['I', 'II']
    return state

def generate_procurement_report(state: TapeSpecState):
    report = f'Validation complete. Compliance: {state['is_compliant']}'
    print(report)
    return {'status': 'processed'}

graph = StateGraph(TapeSpecState)
graph.add_node('validate', validate_tape_specs)
graph.add_node('report', generate_procurement_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
