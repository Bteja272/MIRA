from __future__ import annotations


class ConversationMemoryService:
    FOLLOW_UP_MARKERS = (
        " it ",
        " that ",
        " this ",
        " they ",
        " them ",
        " those ",
        " these ",
        " first ",
        " second ",
        " third ",
        " former ",
        " latter ",
        " previous ",
        " earlier ",
        " same ",
        " what about",
        " how about",
        " more simply",
        " explain that",
        " explain it",
        " compare that",
        " compare it",
    )

    @staticmethod
    def format_context(
        context: (
            list[dict[str, str]]
            | None
        ),
    ) -> str:
        if not context:
            return ""

        lines = [
            "CONVERSATION CONTEXT",
            (
                "The following previous "
                "messages are supplied only "
                "for conversational continuity "
                "and reference resolution."
            ),
            (
                "Do not treat previous assistant "
                "messages as medical evidence."
            ),
            (
                "For document-grounded answers, "
                "medical facts must still come "
                "from the current supplied "
                "document context."
            ),
            "",
        ]

        for message in context:
            role = (
                message.get(
                    "role",
                    "",
                )
                .strip()
                .lower()
            )

            content = (
                message.get(
                    "content",
                    "",
                )
                .strip()
            )

            if (
                role not in {
                    "user",
                    "assistant",
                }
                or not content
            ):
                continue

            label = (
                "User"
                if role == "user"
                else "MIRA"
            )

            lines.append(
                f"{label}: {content}"
            )

        return "\n".join(
            lines
        ).strip()

    @classmethod
    def build_prompt_query(
        cls,
        *,
        query: str,
        context: (
            list[dict[str, str]]
            | None
        ),
    ) -> str:
        formatted_context = (
            cls.format_context(
                context
            )
        )

        if not formatted_context:
            return query

        return (
            f"{formatted_context}\n\n"
            "CURRENT USER QUESTION\n"
            f"{query}"
        )

    @classmethod
    def _looks_like_follow_up(
        cls,
        query: str,
    ) -> bool:
        normalized = (
            " "
            + " ".join(
                query.lower().split()
            )
            + " "
        )

        return any(
            marker in normalized
            for marker
            in cls.FOLLOW_UP_MARKERS
        )

    @classmethod
    def build_retrieval_query(
        cls,
        *,
        query: str,
        context: (
            list[dict[str, str]]
            | None
        ),
    ) -> str:
        if (
            not context
            or not cls
            ._looks_like_follow_up(
                query
            )
        ):
            return query

        previous_user_query = None

        for message in reversed(
            context
        ):
            if (
                message.get("role")
                == "user"
            ):
                content = (
                    message.get(
                        "content",
                        "",
                    )
                    .strip()
                )

                if content:
                    previous_user_query = (
                        content
                    )
                    break

        if not previous_user_query:
            return query

        return (
            "Previous user question: "
            f"{previous_user_query}\n"
            "Current follow-up question: "
            f"{query}"
        )