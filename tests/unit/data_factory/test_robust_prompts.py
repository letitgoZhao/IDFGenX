"""验证 M1 鲁棒 Prompt 的版本化模块边界。"""

from __future__ import annotations

from importlib.util import find_spec
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.resolve import resolve_scenario
from idfgenx.data_factory.disclosure import DisclosurePlan
from idfgenx.data_factory.prompts import (
    PromptFamily,
    load_prompt_config,
    render_all_clean_prompts,
)
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import (
    BuildingUse,
    LengthUnit,
    TemperatureUnit,
    ZoneLayout,
)
from idfgenx.errors import ConfigurationError
import idfgenx.data_factory.robust_prompts as robust_prompts


ROBUST_PROMPT_CONFIG_PATH = Path("configs/prompts/robust_v0_1.json")
CLEAN_PROMPT_CONFIG_PATH = Path("configs/prompts/clean_v0_1.json")


class RobustPromptModuleTests(unittest.TestCase):
    """保护鲁棒 Prompt 配置和实现不被退化为隐式模板。"""

    def test_robust_prompt_module_is_available(self) -> None:
        """删除独立鲁棒渲染边界时必须阻止 M1-008 被误报完成。"""

        self.assertIsNotNone(find_spec("idfgenx.data_factory.robust_prompts"))

    def test_versioned_robust_prompt_config_is_available(self) -> None:
        """遗漏冻结配置时不得从代码内默认值静默生成训练 Prompt。"""

        self.assertTrue(ROBUST_PROMPT_CONFIG_PATH.is_file())

    def test_config_loads_exact_supported_variant_space(self) -> None:
        """缺少任一受控维度或混入未批准噪声时配置契约必须失败。"""

        loader = getattr(robust_prompts, "load_robust_prompt_config", None)
        self.assertIsNotNone(loader)
        if loader is None:
            return

        config = loader(ROBUST_PROMPT_CONFIG_PATH)

        self.assertEqual(config.config_version, "0.1")
        self.assertEqual(
            tuple(family.value for family in config.families),
            ("zh_concise", "zh_expert", "en_concise", "en_expert"),
        )
        self.assertEqual(
            tuple(order.id.value for order in config.clause_orders),
            ("canonical", "constraints_first"),
        )
        self.assertEqual(
            tuple(unit.value for unit in config.length_units),
            ("m", "ft"),
        )
        self.assertEqual(
            tuple(unit.value for unit in config.temperature_units),
            ("degC", "degF"),
        )
        self.assertEqual(
            tuple(item.value for item in config.expression_variants),
            ("standard", "alternate"),
        )
        self.assertEqual(
            tuple(item.value for item in config.controlled_noises),
            ("none", "polite_filler", "context_filler"),
        )

    def test_invalid_noise_set_is_reported_as_configuration_error(self) -> None:
        """配置混入拼写噪声时不得扩张已批准的表层噪声边界。"""

        raw = json.loads(ROBUST_PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
        raw["controlled_noises"].append("typo")
        with TemporaryDirectory() as temporary_directory:
            invalid_path = Path(temporary_directory) / "invalid.json"
            invalid_path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError) as context:
                robust_prompts.load_robust_prompt_config(invalid_path)

        self.assertEqual(context.exception.context["path"], str(invalid_path))

    def test_config_hash_is_stable_for_equivalent_json_key_order(self) -> None:
        """仅调整 JSON 键顺序不得改变鲁棒 Prompt 的追溯哈希。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        raw = json.loads(ROBUST_PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
        reordered = {key: raw[key] for key in reversed(tuple(raw))}
        with TemporaryDirectory() as temporary_directory:
            reordered_path = Path(temporary_directory) / "reordered.json"
            reordered_path.write_text(
                json.dumps(reordered, ensure_ascii=False),
                encoding="utf-8",
            )
            reordered_config = robust_prompts.load_robust_prompt_config(
                reordered_path
            )

        self.assertEqual(
            robust_prompts.robust_prompt_config_sha256(config),
            robust_prompts.robust_prompt_config_sha256(reordered_config),
        )


class RobustPromptBehaviorTests(unittest.TestCase):
    """验证鲁棒变体的文本、训练目标和确定性语义保持一致。"""

    @staticmethod
    def _spec() -> ResolvedScenarioSpec:
        """返回包含全部 Prompt 字段的 SI-only 建筑事实。"""

        return ResolvedScenarioSpec(
            building_name="Demo",
            length_m=20,
            width_m=10,
            floor_to_floor_height_m=3,
            stories=2,
            zone_layout=ZoneLayout.SINGLE,
            perimeter_depth_m=None,
            window_to_wall_ratio=0.4,
            heating_setpoint_c=20,
            cooling_setpoint_c=26,
            building_use=BuildingUse.OFFICE,
        )

    def test_imperial_expert_variant_round_trips_to_same_building_fact(self) -> None:
        """仅替换 Prompt 单位却保留 SI Draft 时本测试必须失败。"""

        plan_type = getattr(robust_prompts, "RobustPromptPlan", None)
        renderer = getattr(robust_prompts, "render_robust_prompt", None)
        self.assertIsNotNone(plan_type)
        self.assertIsNotNone(renderer)
        if plan_type is None or renderer is None:
            return
        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = plan_type(
            length_unit=LengthUnit.FOOT,
            temperature_unit=TemperatureUnit.FAHRENHEIT,
            clause_order=robust_prompts.ClauseOrder.CONSTRAINTS_FIRST,
            expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
            controlled_noise=robust_prompts.ControlledNoise.POLITE_FILLER,
        )

        record = renderer(
            self._spec(),
            DisclosurePlan(frozenset(config.clause_orders[0].fields)),
            PromptFamily.EN_EXPERT,
            plan,
            config,
        )

        self.assertEqual(
            record.prompt,
            (
                "Please create an EnergyPlus v23.1 building scenario. "
                'Project identifier: "Demo"; occupancy archetype: office; '
                "heating thermostat setpoint: 68 °F; cooling thermostat setpoint: "
                "78.8 °F; WWR: 0.4; thermal zoning: single zone; floor count: 2; "
                "plan length: 65.6167979003 ft; plan width: 32.8083989501 ft; "
                "floor-to-floor dimension: 9.84251968504 ft. Apply system defaults "
                "to unspecified fields."
            ),
        )
        self.assertEqual(record.scenario_spec_draft_target.length.unit, LengthUnit.FOOT)
        self.assertEqual(
            record.scenario_spec_draft_target.heating_setpoint.unit,
            TemperatureUnit.FAHRENHEIT,
        )
        self.assertEqual(
            record.scenario_spec_draft_target.length.value,
            65.6167979003,
        )
        self.assertEqual(resolve_scenario(record.scenario_spec_draft_target), self._spec())
        self.assertEqual(
            record.variant_id,
            "en_expert.ft.degF.constraints_first.alternate.polite_filler",
        )

    def test_standard_si_variants_preserve_all_clean_family_outputs(self) -> None:
        """鲁棒基线改写任一冻结 clean Prompt 时兼容性测试必须失败。"""

        renderer = getattr(robust_prompts, "render_all_robust_prompts", None)
        self.assertIsNotNone(renderer)
        if renderer is None:
            return
        robust_config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.METER,
            temperature_unit=TemperatureUnit.CELSIUS,
            clause_order=robust_prompts.ClauseOrder.CANONICAL,
            expression_variant=robust_prompts.ExpressionVariant.STANDARD,
            controlled_noise=robust_prompts.ControlledNoise.NONE,
        )

        robust_records = renderer(
            self._spec(),
            DisclosurePlan(frozenset(robust_config.clause_orders[0].fields)),
            plan,
            robust_config,
        )
        clean_records = render_all_clean_prompts(
            self._spec(),
            load_prompt_config(CLEAN_PROMPT_CONFIG_PATH),
        )

        self.assertEqual(
            tuple(record.prompt for record in robust_records),
            tuple(record.prompt for record in clean_records),
        )
        self.assertEqual(
            tuple(record.scenario_spec_draft_target for record in robust_records),
            tuple(record.scenario_spec_draft_target for record in clean_records),
        )
        self.assertEqual(
            tuple(record.family for record in robust_records),
            tuple(PromptFamily),
        )

    def test_alternate_context_variant_supports_all_four_families(self) -> None:
        """任一语言或风格退回只支持单个专家模板时本测试必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.FOOT,
            temperature_unit=TemperatureUnit.FAHRENHEIT,
            clause_order=robust_prompts.ClauseOrder.CONSTRAINTS_FIRST,
            expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
            controlled_noise=robust_prompts.ControlledNoise.CONTEXT_FILLER,
        )
        disclosure_plan = DisclosurePlan(
            frozenset(config.clause_orders[0].fields)
        )

        first = robust_prompts.render_all_robust_prompts(
            self._spec(), disclosure_plan, plan, config
        )
        second = robust_prompts.render_all_robust_prompts(
            self._spec(), disclosure_plan, plan, config
        )

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(record.family for record in first),
            tuple(PromptFamily),
        )
        expected_fragments = {
            PromptFamily.ZH_CONCISE: (
                "项目名“Demo”",
                "供暖温控点68 °F",
                "平面长度65.6167979003 ft",
                "这是概念设计阶段的输入。",
            ),
            PromptFamily.ZH_EXPERT: (
                "项目标识：“Demo”",
                "供暖恒温器设定点：68 °F",
                "平面长度：65.6167979003 ft",
                "这是概念设计阶段的输入。",
            ),
            PromptFamily.EN_CONCISE: (
                'project "Demo"',
                "heating target 68 °F",
                "plan length 65.6167979003 ft",
                "This is conceptual-design context.",
            ),
            PromptFamily.EN_EXPERT: (
                'Project identifier: "Demo"',
                "heating thermostat setpoint: 68 °F",
                "plan length: 65.6167979003 ft",
                "This is conceptual-design context.",
            ),
        }
        for record in first:
            identity, heating, length, context = expected_fragments[record.family]
            self.assertIn(identity, record.prompt)
            self.assertIn(heating, record.prompt)
            self.assertIn(length, record.prompt)
            self.assertTrue(record.prompt.endswith(context))
            self.assertLess(record.prompt.index(heating), record.prompt.index(length))
            self.assertEqual(
                record.controlled_noise,
                robust_prompts.ControlledNoise.CONTEXT_FILLER,
            )

    def test_standard_variant_composes_units_order_and_polite_noise(self) -> None:
        """standard 表达只能用于 clean 基线时独立变体契约必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.FOOT,
            temperature_unit=TemperatureUnit.FAHRENHEIT,
            clause_order=robust_prompts.ClauseOrder.CONSTRAINTS_FIRST,
            expression_variant=robust_prompts.ExpressionVariant.STANDARD,
            controlled_noise=robust_prompts.ControlledNoise.POLITE_FILLER,
        )

        records = robust_prompts.render_all_robust_prompts(
            self._spec(),
            DisclosurePlan(frozenset(config.clause_orders[0].fields)),
            plan,
            config,
        )

        expected_fragments = {
            PromptFamily.ZH_CONCISE: (
                "麻烦",
                "供暖设定温度为68 °F",
                "长65.6167979003 ft",
            ),
            PromptFamily.ZH_EXPERT: (
                "麻烦",
                "供暖设定温度：68 °F",
                "建筑长度：65.6167979003 ft",
            ),
            PromptFamily.EN_CONCISE: (
                "Please ",
                "a heating setpoint of 68 °F",
                "65.6167979003 ft long",
            ),
            PromptFamily.EN_EXPERT: (
                "Please ",
                "heating setpoint: 68 °F",
                "building length: 65.6167979003 ft",
            ),
        }
        for record in records:
            prefix, heating, length = expected_fragments[record.family]
            self.assertTrue(record.prompt.startswith(prefix))
            self.assertIn(heating, record.prompt)
            self.assertIn(length, record.prompt)
            self.assertLess(record.prompt.index(heating), record.prompt.index(length))

    def test_polite_noise_never_makes_requested_fields_conditional(self) -> None:
        """礼貌噪声引入“如条件允许”语义时 requested 标签必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.METER,
            temperature_unit=TemperatureUnit.CELSIUS,
            clause_order=robust_prompts.ClauseOrder.CANONICAL,
            expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
            controlled_noise=robust_prompts.ControlledNoise.POLITE_FILLER,
        )
        records = robust_prompts.render_all_robust_prompts(
            self._spec(),
            DisclosurePlan(frozenset(config.clause_orders[0].fields)),
            plan,
            config,
        )

        for record in records[:2]:
            self.assertTrue(record.prompt.startswith("麻烦"))
            self.assertNotIn("如条件允许", record.prompt)
        for record in records[2:]:
            self.assertTrue(record.prompt.startswith("Please "))
            self.assertNotIn("If possible", record.prompt)

    def test_expert_chinese_preserves_floor_to_floor_height_semantics(self) -> None:
        """把 floor-to-floor height 错写为建筑净高时语义测试必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        record = robust_prompts.render_robust_prompt(
            self._spec(),
            DisclosurePlan(frozenset({"floor_to_floor_height"})),
            PromptFamily.ZH_EXPERT,
            robust_prompts.RobustPromptPlan(
                length_unit=LengthUnit.METER,
                temperature_unit=TemperatureUnit.CELSIUS,
                clause_order=robust_prompts.ClauseOrder.CANONICAL,
                expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
                controlled_noise=robust_prompts.ControlledNoise.NONE,
            ),
            config,
        )

        self.assertIn("楼层层高：3 m", record.prompt)
        self.assertNotIn("净高", record.prompt)

    def test_noncanonical_numeric_precision_is_rejected_before_label_drift(self) -> None:
        """Prompt 文本量化 requested 数值却保留不同标签时门禁必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        high_precision_spec = self._spec().model_copy(
            update={
                "length_m": 20.123456789012345,
                "window_to_wall_ratio": 0.4123456789012345,
            }
        )

        with self.assertRaises(ConfigurationError) as context:
            robust_prompts.render_robust_prompt(
                high_precision_spec,
                DisclosurePlan(frozenset(config.clause_orders[0].fields)),
                PromptFamily.EN_EXPERT,
                robust_prompts.RobustPromptPlan(
                    length_unit=LengthUnit.METER,
                    temperature_unit=TemperatureUnit.CELSIUS,
                    clause_order=robust_prompts.ClauseOrder.CANONICAL,
                    expression_variant=robust_prompts.ExpressionVariant.STANDARD,
                    controlled_noise=robust_prompts.ControlledNoise.NONE,
                ),
                config,
            )

        self.assertEqual(
            context.exception.context["fields"],
            ["length", "window_to_wall_ratio"],
        )

    def test_full_disclosure_rejects_unrepresentable_perimeter_depth(self) -> None:
        """Draft 无深度字段却接受非派生 perimeter 深度时往返门禁必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        noncanonical_spec = ResolvedScenarioSpec(
            building_name="Core",
            length_m=20,
            width_m=16,
            floor_to_floor_height_m=3,
            stories=2,
            zone_layout=ZoneLayout.PERIMETER_CORE,
            perimeter_depth_m=3,
            window_to_wall_ratio=0.4,
            heating_setpoint_c=20,
            cooling_setpoint_c=26,
            building_use=BuildingUse.OFFICE,
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.METER,
            temperature_unit=TemperatureUnit.CELSIUS,
            clause_order=robust_prompts.ClauseOrder.CANONICAL,
            expression_variant=robust_prompts.ExpressionVariant.STANDARD,
            controlled_noise=robust_prompts.ControlledNoise.NONE,
        )
        full_disclosure = DisclosurePlan(
            frozenset(config.clause_orders[0].fields)
        )

        with self.assertRaises(ConfigurationError) as context:
            robust_prompts.render_robust_prompt(
                noncanonical_spec,
                full_disclosure,
                PromptFamily.EN_EXPERT,
                plan,
                config,
            )

        self.assertEqual(context.exception.context["actual_depth_m"], 3.0)
        self.assertEqual(context.exception.context["expected_depth_m"], 4.0)

        canonical_spec = noncanonical_spec.model_copy(
            update={"perimeter_depth_m": 4.0}
        )
        record = robust_prompts.render_robust_prompt(
            canonical_spec,
            full_disclosure,
            PromptFamily.EN_EXPERT,
            plan,
            config,
        )
        self.assertEqual(
            resolve_scenario(record.scenario_spec_draft_target),
            canonical_spec,
        )

    def test_unsafe_building_name_is_rejected_for_alternate_expression(self) -> None:
        """alternate renderer 绕过名称分隔符门禁时本测试必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.METER,
            temperature_unit=TemperatureUnit.CELSIUS,
            clause_order=robust_prompts.ClauseOrder.CANONICAL,
            expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
            controlled_noise=robust_prompts.ControlledNoise.NONE,
        )
        unsafe_spec = self._spec().model_copy(
            update={"building_name": 'A\nB；C"D'}
        )

        with self.assertRaises(ConfigurationError) as context:
            robust_prompts.render_robust_prompt(
                unsafe_spec,
                DisclosurePlan(frozenset({"building_name"})),
                PromptFamily.ZH_EXPERT,
                plan,
                config,
            )

        self.assertEqual(context.exception.context["building_name"], 'A\nB；C"D')

    def test_all_declared_variant_combinations_are_deterministic(self) -> None:
        """任一配置声明组合无法生成或改变 SI 建筑事实时本测试必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        disclosure_plan = DisclosurePlan(
            frozenset(config.clause_orders[0].fields)
        )
        plan_count = 0
        record_count = 0
        for length_unit in config.length_units:
            for temperature_unit in config.temperature_units:
                for clause_order in config.clause_orders:
                    for expression in config.expression_variants:
                        for noise in config.controlled_noises:
                            plan = robust_prompts.RobustPromptPlan(
                                length_unit=length_unit,
                                temperature_unit=temperature_unit,
                                clause_order=clause_order.id,
                                expression_variant=expression,
                                controlled_noise=noise,
                            )
                            with self.subTest(plan=plan):
                                first = robust_prompts.render_all_robust_prompts(
                                    self._spec(), disclosure_plan, plan, config
                                )
                                second = robust_prompts.render_all_robust_prompts(
                                    self._spec(), disclosure_plan, plan, config
                                )
                                self.assertEqual(first, second)
                                self.assertEqual(len(first), 4)
                                self.assertTrue(
                                    all(
                                        resolve_scenario(
                                            record.scenario_spec_draft_target
                                        )
                                        == self._spec()
                                        for record in first
                                    )
                                )
                            plan_count += 1
                            record_count += len(config.families)

        self.assertEqual(plan_count, 48)
        self.assertEqual(record_count, 192)

    def test_partial_disclosure_never_leaks_or_converts_defaulted_fields(self) -> None:
        """未披露字段进入 Prompt 或获得单位时诚实标签门禁必须失败。"""

        config = robust_prompts.load_robust_prompt_config(
            ROBUST_PROMPT_CONFIG_PATH
        )
        plan = robust_prompts.RobustPromptPlan(
            length_unit=LengthUnit.FOOT,
            temperature_unit=TemperatureUnit.FAHRENHEIT,
            clause_order=robust_prompts.ClauseOrder.CONSTRAINTS_FIRST,
            expression_variant=robust_prompts.ExpressionVariant.ALTERNATE,
            controlled_noise=robust_prompts.ControlledNoise.CONTEXT_FILLER,
        )

        record = robust_prompts.render_robust_prompt(
            self._spec(),
            DisclosurePlan(frozenset({"building_name", "length"})),
            PromptFamily.ZH_CONCISE,
            plan,
            config,
        )

        self.assertIn("65.6167979003 ft", record.prompt)
        self.assertNotIn("32.8083989501", record.prompt)
        self.assertNotIn("78.8", record.prompt)
        self.assertIsNone(record.scenario_spec_draft_target.width.unit)
        self.assertIsNone(record.scenario_spec_draft_target.width.value)


if __name__ == "__main__":
    unittest.main()
