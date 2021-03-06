from ....models.models import Motion
from ...generics.update import UpdateAction
from ...mixins.linear_sort_mixin import LinearSortMixin
from ...mixins.singular_action_mixin import SingularActionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload


@register_action("motion_category.sort_motions_in_category")
class MotionCategorySortMotionInCategorySort(
    LinearSortMixin, SingularActionMixin, UpdateAction
):
    """
    Action to motion category sort motions in categories.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_linear_sort_schema("motion_ids", "id")

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        payload = super().get_updated_instances(payload)
        # Payload is an iterable with exactly one item
        instance = next(iter(payload))
        yield from self.sort_linear(
            nodes=instance["motion_ids"],
            filter_id=instance["id"],
            filter_str="category_id",
            weight_key="category_weight",
        )
