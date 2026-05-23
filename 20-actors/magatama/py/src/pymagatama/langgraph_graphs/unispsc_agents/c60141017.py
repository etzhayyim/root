from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KaleidoscopeState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_optics(state: KaleidoscopeState):
    log = state.get('validation_log', [])
    has_glass = state['specs'].get('glass_quality') == 'optical'
    log.append(f'Optical validation: {has_glass}')
    return {'validation_log': log, 'approved': has_glass}

def finalize_order(state: KaleidoscopeState):
    return {'validation_log': state['validation_log'] + ['Order validated for procurement']}

graph = StateGraph(KaleidoscopeState)
graph.add_node('validate', validate_optics)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
