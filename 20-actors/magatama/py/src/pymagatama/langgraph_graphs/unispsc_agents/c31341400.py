from typing import TypedDict
from langgraph.graph import StateGraph, END
class AssemblyState(TypedDict):
    weld_parameters: dict
    validation_passed: bool
def validate_welds(state: AssemblyState):
    freq = state['weld_parameters'].get('freq', 0)
    return {'validation_passed': freq > 20000}
def report_status(state: AssemblyState):
    print(f'Validation result: {state['validation_passed']}')
    return {}
graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_welds)
graph.add_node('report', report_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
