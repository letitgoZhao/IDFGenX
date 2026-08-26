import unittest

from idfgenx.data_factory.disclosure import default_disclosure_plan, derive_draft
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, FieldStatus, ZoneLayout


class DisclosurePlanTests(unittest.TestCase):
    def test_derivation_marks_defaults_without_claiming_user_request(self) -> None:
        spec = ResolvedScenarioSpec(building_name="Demo", length_m=20, width_m=10, floor_to_floor_height_m=3, stories=2, zone_layout=ZoneLayout.SINGLE, perimeter_depth_m=None, window_to_wall_ratio=.4, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
        draft = derive_draft(spec, default_disclosure_plan())
        self.assertEqual(draft.length.status, FieldStatus.DEFAULTED)
        self.assertIsNone(draft.length.value)

    def test_plan_can_disclose_requested_length_with_unit(self) -> None:
        spec = ResolvedScenarioSpec(building_name="Demo", length_m=20, width_m=10, floor_to_floor_height_m=3, stories=2, zone_layout=ZoneLayout.SINGLE, perimeter_depth_m=None, window_to_wall_ratio=.4, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
        draft = derive_draft(spec, type(default_disclosure_plan())(frozenset({"length"})))
        self.assertEqual(draft.length.status, FieldStatus.REQUESTED)
        self.assertEqual(draft.length.value, 20)
