"""ScenarioSpecDraft 到 ResolvedScenarioSpec 的 Resolver 契约测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.resolve import resolve_scenario
from idfgenx.errors import ErrorCode, ResolutionError
from idfgenx.schemas.scenario import (
    DraftQuantity,
    DraftValue,
    FieldStatus,
    LengthUnit,
    ScenarioSpecDraft,
    TemperatureUnit,
    ZoneLayout,
)


class ScenarioResolverTests(unittest.TestCase):
    """验证唯一 Resolver 负责换算、默认、派生和拒绝。"""

    def test_resolver_converts_requested_imperial_values_to_si(self) -> None:
        """若转换留在 Compiler 或使用错误系数，此测试会失败。"""

        resolved = resolve_scenario(
            ScenarioSpecDraft(
                length=DraftQuantity(
                    value=40.0,
                    unit=LengthUnit.FOOT,
                    status=FieldStatus.REQUESTED,
                ),
                width=DraftQuantity(
                    value=20.0,
                    unit=LengthUnit.FOOT,
                    status=FieldStatus.REQUESTED,
                ),
                heating_setpoint=DraftQuantity(
                    value=68.0,
                    unit=TemperatureUnit.FAHRENHEIT,
                    status=FieldStatus.REQUESTED,
                ),
            )
        )

        self.assertEqual(resolved.length_m, 12.192)
        self.assertEqual(resolved.width_m, 6.096)
        self.assertEqual(resolved.heating_setpoint_c, 20.0)
        self.assertEqual(resolved.cooling_setpoint_c, 26.0)
        self.assertEqual(resolved.stories, 1)

    def test_resolver_derives_perimeter_depth_from_short_side(self) -> None:
        """遗漏周边核心深度派生会使后续多区几何没有唯一输入。"""

        resolved = resolve_scenario(
            ScenarioSpecDraft(
                length=DraftQuantity(
                    value=20.0,
                    unit=LengthUnit.METER,
                    status=FieldStatus.REQUESTED,
                ),
                width=DraftQuantity(
                    value=16.0,
                    unit=LengthUnit.METER,
                    status=FieldStatus.REQUESTED,
                ),
                zone_layout=DraftValue(
                    value=ZoneLayout.PERIMETER_CORE,
                    status=FieldStatus.REQUESTED,
                ),
            )
        )

        self.assertEqual(resolved.perimeter_depth_m, 4.0)

    def test_resolver_rejects_unresolved_status_with_stable_error(self) -> None:
        """将歧义字段静默默认会导致模型输出越过能力边界。"""

        draft = ScenarioSpecDraft(
            length=DraftQuantity(status=FieldStatus.AMBIGUOUS),
        )

        with self.assertRaises(ResolutionError) as caught:
            resolve_scenario(draft)

        self.assertEqual(caught.exception.code, ErrorCode.RESOLUTION_FAILED)
        self.assertEqual(caught.exception.context["field"], "length")


if __name__ == "__main__":
    unittest.main()
