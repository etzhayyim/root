from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class AnalysisState(TypedDict):
    device_id: str
    readings: List[float]
    passed: bool
class AnalyzerProcessor:
    def validate(self, state: AnalysisState):
        state['passed'] = all(0 <= r <= 100 for r in state['readings'])
        return state
define_graph = StateGraph(AnalysisState)
define_graph.add_node('validate_data', AnalyzerProcessor().validate)
define_graph.set_entry_point('validate_data')
define_graph.add_edge('validate_data', END)
graph = define_graph.compile()
