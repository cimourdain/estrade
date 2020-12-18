from estrade import Epic


def test_create_epic():
    epic = Epic(ref="MY_EPIC_REF")

    assert epic.ref == "MY_EPIC_REF"
