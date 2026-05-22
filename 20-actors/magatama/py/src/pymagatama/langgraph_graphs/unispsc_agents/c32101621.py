from typing import TypedDict, List
from langgraph.graph import StateGraph, END


class SDRAMState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool


def validate_memory(state: SDRAMState):
    errors = []
    freq = state['specs'].get('frequency', 0)
    if freq < 1600:
        errors.append('Frequency below minimum threshold')
    return {'validation_errors': errors, 'approved': len(errors) == 0}


graph = StateGraph(SDRAMState)
graph.add_node('validate', validate_memory)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
