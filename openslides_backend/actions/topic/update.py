from typing import Any

import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...shared.exceptions import PermissionDenied
from ...shared.interfaces import Event, WriteRequestElement
from ...shared.patterns import FullQualifiedField, FullQualifiedId
from ...shared.permissions.topic import TOPIC_CAN_MANAGE
from ...shared.schema import schema_version
from ..actions import register_action
from ..actions_interface import Payload
from ..base import Action, DataSet

update_topic_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Update topics schema",
        "description": "An array of topics to be updated.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": Topic().get_schema("id"),
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "mediafile_attachment_ids": Topic().get_schema(
                    "mediafile_attachment_ids"
                ),
            },
            "required": ["id"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


@register_action("topic.update")
class TopicUpdate(Action):
    """
    Action to update simple topics that can be shown in the agenda.
    """

    model = Topic()
    schema = update_topic_schema

    def check_permission(self, meeting_id: int) -> None:
        required_permission = f"{meeting_id}/{TOPIC_CAN_MANAGE}"
        if not self.permission.has_perm(self.user_id, required_permission):
            raise PermissionDenied(
                f"User does not have {TOPIC_CAN_MANAGE} permission for meeting {meeting_id}."
            )

    def prepare_dataset(self, payload: Payload) -> DataSet:
        data = []
        for topic in payload:
            db_topic, position = self.database.get(
                fqid=FullQualifiedId(self.model.collection, id=topic["id"]),
                mapped_fields=["meeting_id"],
            )
            self.set_min_position(position)
            self.check_permission(db_topic["meeting_id"])
            references = self.get_references(
                model=self.model,
                id=topic["id"],
                obj=topic,
                field_names=["mediafile_attachment_ids"],
                deletion_possible=True,
            )
            data.append({"topic": topic, "references": references})
        return {"position": self.position, "data": data}

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        fqfields = {}
        for field in element["topic"].keys():
            if field == "id":
                continue
            fqfields[
                FullQualifiedField(self.model.collection, element["topic"]["id"], field)
            ] = element["topic"][field]
        information = {
            FullQualifiedId(self.model.collection, element["topic"]["id"]): [
                "Topic updated"
            ]
        }
        event = Event(type="update", fqfields=fqfields)
        return WriteRequestElement(
            events=[event],
            information=information,
            user_id=self.user_id,
            locked_fields={
                FullQualifiedField(
                    self.model.collection, element["topic"]["id"], "deleted"
                ): position
            },
        )
