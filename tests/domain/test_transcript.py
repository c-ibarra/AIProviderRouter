from router.domain.transcript import Transcript


def test_from_messages_extracts_system_and_turns():
    messages = [
        {"role": "system", "content": "You are terse."},
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "How are you?"},
    ]

    transcript = Transcript.from_messages(messages)

    assert transcript.system == "You are terse."
    assert [(t.role, t.content) for t in transcript.turns] == [
        ("user", "Hi"),
        ("assistant", "Hello"),
        ("user", "How are you?"),
    ]


def test_from_messages_without_system_message():
    messages = [{"role": "user", "content": "Hi"}]

    transcript = Transcript.from_messages(messages)

    assert transcript.system is None
    assert [(t.role, t.content) for t in transcript.turns] == [("user", "Hi")]


def test_flatten_includes_system_and_turns_in_order():
    transcript = Transcript.from_messages(
        [
            {"role": "system", "content": "Be terse."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Bye"},
        ]
    )

    flattened = transcript.flatten()

    assert flattened == (
        "System: Be terse.\n\n"
        "User: Hi\n"
        "Assistant: Hello\n"
        "User: Bye"
    )


def test_flatten_without_system_message_has_no_system_line():
    transcript = Transcript.from_messages([{"role": "user", "content": "Hi"}])

    flattened = transcript.flatten()

    assert flattened == "User: Hi"
    assert "System:" not in flattened


def test_flatten_turns_only_excludes_system_line():
    transcript = Transcript.from_messages(
        [
            {"role": "system", "content": "Be terse."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Bye"},
        ]
    )

    flattened = transcript.flatten_turns_only()

    assert flattened == "User: Hi\nAssistant: Hello\nUser: Bye"
    assert "System:" not in flattened
