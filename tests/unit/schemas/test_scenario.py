"""ScenarioSpecDraft v0.1 的领域契约测试。"""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from idfgenx.schemas.scenario import (
    BuildingUse,
    DraftQuantity,
    DraftValue,
    FieldStatus,
    LengthUnit,
    ScenarioSpecDraft,
    TemperatureUnit,
    ZoneLayout,
)


class ScenarioSpecDraftTests(unittest.TestCase):
    """验证 Draft 保留用户输入的原始值、单位和字段状态。"""

    def test_requested_values_are_serialized_without_unit_conversion(self) -> None:
        """错误地在 Draft 中换算英尺会使此契约测试失败。"""

        draft = ScenarioSpecDraft(
            building_name=DraftValue(value="教学楼 A", status=FieldStatus.REQUESTED),
            length=DraftQuantity(
                value=40.0,
                unit=LengthUnit.FOOT,
                status=FieldStatus.REQUESTED,
            ),
            width=DraftQuantity(
                value=24.0,
                unit=LengthUnit.METER,
                status=FieldStatus.REQUESTED,
            ),
            floor_to_floor_height=DraftQuantity(
                value=3.6,
                unit=LengthUnit.METER,
                status=FieldStatus.REQUESTED,
            ),
            stories=DraftValue(value=2, status=FieldStatus.REQUESTED),
            zone_layout=DraftValue(
                value=ZoneLayout.SINGLE,
                status=FieldStatus.REQUESTED,
            ),
            window_to_wall_ratio=DraftValue(
                value=0.4,
                status=FieldStatus.REQUESTED,
            ),
            heating_setpoint=DraftQuantity(
                value=68.0,
                unit=TemperatureUnit.FAHRENHEIT,
                status=FieldStatus.REQUESTED,
            ),
            cooling_setpoint=DraftQuantity(
                value=25.0,
                unit=TemperatureUnit.CELSIUS,
                status=FieldStatus.REQUESTED,
            ),
            building_use=DraftValue(
                value=BuildingUse.CLASSROOM,
                status=FieldStatus.REQUESTED,
            ),
        )

        payload = draft.model_dump(mode="json")

        self.assertEqual(payload["schema_version"], "0.1")
        self.assertEqual(payload["length"], {"value": 40.0, "unit": "ft", "status": "requested"})
        self.assertEqual(
            payload["heating_setpoint"],
            {"value": 68.0, "unit": "degF", "status": "requested"},
        )

    def test_defaulted_field_must_not_claim_a_value(self) -> None:
        """默认值若在 Draft 提前注入，会掩盖用户是否实际给出该字段。"""

        with self.assertRaises(ValidationError):
            DraftValue(value=0.4, status=FieldStatus.DEFAULTED)

    def test_ambiguous_field_must_not_carry_a_numeric_interpretation(self) -> None:
        """歧义字段携带数值会让 Resolver 无法区分用户原意与猜测。"""

        with self.assertRaises(ValidationError):
            DraftQuantity(
                value=20.0,
                unit=LengthUnit.METER,
                status=FieldStatus.AMBIGUOUS,
            )

    def test_schema_export_fixes_v01_contract_and_forbids_unknown_fields(self) -> None:
        """移除版本常量或允许未知字段会破坏模型训练与下游解析契约。"""

        schema = ScenarioSpecDraft.model_json_schema()

        self.assertEqual(schema["properties"]["schema_version"]["const"], "0.1")
        with self.assertRaises(ValidationError):
            ScenarioSpecDraft.model_validate({"unexpected": "field"})


if __name__ == "__main__":
    unittest.main()
