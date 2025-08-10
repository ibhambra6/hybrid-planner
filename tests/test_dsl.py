from dsl.parse_llm import parse_text_to_task


def test_parse_basic():
    task = parse_text_to_task("please put the red mug on the shelf")
    assert task.goal == "tidy_table"
    assert len(task.steps) == 3
    assert task.steps[0].action == "perceive"
    assert task.steps[1].action == "grasp"
    assert task.steps[2].action == "place"


