from dsl.parse_llm import parse_text_to_task
from envs.table_top import TableTopSim
from executor.executor import Executor


def test_executor_end_to_end():
    env = TableTopSim(use_gui=False)
    ex = Executor(env)
    task = parse_text_to_task("tidy the red mug on the shelf")
    result = ex.run(task.model_dump(), timeout_s=10.0, retries=0)
    assert result.metrics.success


