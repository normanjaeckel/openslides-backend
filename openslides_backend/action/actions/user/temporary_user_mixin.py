from typing import Any, Dict

from ....models.models import User
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ...action import Action


class TemporaryUserMixin(Action):
    def update_instance_temporary_user(
        self, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        present_in_meeting_ids = instance.get("is_present_in_meeting_ids")
        if present_in_meeting_ids and any(
            id != instance["meeting_id"] for id in present_in_meeting_ids
        ):
            raise ActionException(
                "A temporary user can only be present in its respective meeting."
            )

        if "group_ids" in instance:
            self.check_equal_fields(
                User.group__ids, instance, "group_ids", ["meeting_id"]
            )
            group_ids = instance.pop("group_ids")
            instance[f"group_${instance['meeting_id']}_ids"] = group_ids

        if "vote_delegations_from_ids" in instance:
            vote_delegations_from_ids = instance.pop("vote_delegations_from_ids")
            get_many_request = GetManyRequest(
                self.model.collection, vote_delegations_from_ids, ["id"]
            )
            gm_result = self.datastore.get_many([get_many_request])
            users = gm_result.get(self.model.collection, {})

            set_payload = set(vote_delegations_from_ids)
            diff = set_payload.difference(users.keys())
            if len(diff):
                raise ActionException(f"The following users were not found: {diff}")

            instance[
                f"vote_delegations_${instance['meeting_id']}_from_ids"
            ] = vote_delegations_from_ids

        return instance
