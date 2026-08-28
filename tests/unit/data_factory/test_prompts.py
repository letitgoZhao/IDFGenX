"""验证 M1 clean Prompt 配置和渲染契约。"""

from __future__ import annotations

from importlib.util import find_spec
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.data_factory.disclosure import DisclosurePlan
from idfgenx.errors import ConfigurationError
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, FieldStatus, ZoneLayout
import idfgenx.data_factory.prompts as prompts


PROMPT_CONFIG_PATH = Path("configs/prompts/clean_v0_1.json")
PUBLIC_CONTRACT = (
    "PromptFamily",
    "PromptLanguage",
    "PromptStyle",
    "PromptConfig",
    "CleanPromptRecord",
    "load_prompt_config",
    "prompt_config_sha256",
    "prompt_disclosure_plan",
    "render_clean_prompt",
    "render_all_clean_prompts",
)
CONTRACT_AVAILABLE = all(hasattr(prompts, name) for name in PUBLIC_CONTRACT)


class CleanPromptModuleTests(unittest.TestCase):
    """保护 clean Prompt 功能拥有独立且可导入的模块边界。"""

    def test_prompt_module_is_available(self) -> None:
        """缺失 Prompt 模块时应阻止 M1-007 被误报为已实现。"""

        self.assertIsNotNone(find_spec("idfgenx.data_factory.prompts"))

    def test_prompt_module_exposes_typed_rendering_contract(self) -> None:
        """删除任一公共配置或渲染入口都必须破坏模块契约测试。"""

        missing = [name for name in PUBLIC_CONTRACT if not hasattr(prompts, name)]
        self.assertEqual(missing, [])

    def test_versioned_prompt_config_is_available(self) -> None:
        """遗漏冻结配置文件时数据构建不得退回代码内隐式默认值。"""

        self.assertTrue(PROMPT_CONFIG_PATH.is_file())


@unittest.skipUnless(
    CONTRACT_AVAILABLE and PROMPT_CONFIG_PATH.is_file(),
    "Prompt 公共契约或版本化配置尚未实现",
)
class CleanPromptBehaviorTests(unittest.TestCase):
    """验证四个 clean family 的用户可见行为与披露边界。"""

    @staticmethod
    def _spec() -> ResolvedScenarioSpec:
        """返回包含所有 v0.1 Prompt 字段的手工场景。"""

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

    def test_config_loads_exactly_four_clean_families(self) -> None:
        """缺少、重复或混入 noisy family 时配置门禁必须失败。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)

        self.assertEqual(config.config_version, "0.1")
        self.assertEqual(
            tuple(family.id.value for family in config.families),
            ("zh_concise", "zh_expert", "en_concise", "en_expert"),
        )
        self.assertEqual(
            config.requested_fields,
            (
                "building_name",
                "building_use",
                "length",
                "width",
                "floor_to_floor_height",
                "stories",
                "zone_layout",
                "window_to_wall_ratio",
                "heating_setpoint",
                "cooling_setpoint",
            ),
        )

    def test_config_hash_is_independent_of_json_key_order(self) -> None:
        """仅调整 JSON 键顺序不得改变 release 使用的 Prompt 配置哈希。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        raw = json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
        reordered = {key: raw[key] for key in reversed(tuple(raw))}
        with TemporaryDirectory() as temporary_directory:
            reordered_path = Path(temporary_directory) / "reordered.json"
            reordered_path.write_text(
                json.dumps(reordered, ensure_ascii=False),
                encoding="utf-8",
            )
            reordered_config = prompts.load_prompt_config(reordered_path)

        self.assertEqual(
            prompts.prompt_config_sha256(config),
            prompts.prompt_config_sha256(reordered_config),
        )

    def test_invalid_family_set_is_reported_as_configuration_error(self) -> None:
        """删掉英文专家模板时加载器必须给出项目统一配置错误。"""

        raw = json.loads(PROMPT_CONFIG_PATH.read_text(encoding="utf-8"))
        raw["families"] = raw["families"][:-1]
        with TemporaryDirectory() as temporary_directory:
            invalid_path = Path(temporary_directory) / "invalid.json"
            invalid_path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigurationError) as context:
                prompts.load_prompt_config(invalid_path)

        self.assertEqual(context.exception.context["path"], str(invalid_path))

    def test_four_families_render_stable_clean_prompts(self) -> None:
        """错误语言、术语、单位或字段顺序必须使字面输出断言失败。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        records = prompts.render_all_clean_prompts(self._spec(), config)

        self.assertEqual(
            {record.family.value: record.prompt for record in records},
            {
                "zh_concise": (
                    "请生成一栋名称为“Demo”、用途为办公、长20 m、宽10 m、层高3 m、"
                    "共2层、采用单区布局、窗墙比为0.4、供暖设定温度为20 °C、"
                    "制冷设定温度为26 °C的建筑模型；其余参数使用系统默认值。"
                ),
                "zh_expert": (
                    "请为 EnergyPlus v23.1 建立建筑场景。建筑名称：“Demo”；建筑用途：办公；"
                    "建筑长度：20 m；建筑宽度：10 m；层高：3 m；层数：2；热区布局：单区；"
                    "窗墙比（WWR）：0.4；供暖设定温度：20 °C；制冷设定温度：26 °C。"
                    "未明确字段按系统默认处理。"
                ),
                "en_concise": (
                    'Generate a building model named "Demo", used as an office, '
                    "20 m long, 10 m wide, with a 3 m floor-to-floor height, "
                    "2 stories, a single-zone layout, a window-to-wall ratio of 0.4, "
                    "a heating setpoint of 20 °C, and a cooling setpoint of 26 °C. "
                    "Use system defaults for unspecified parameters."
                ),
                "en_expert": (
                    'Create an EnergyPlus v23.1 building scenario. Building name: "Demo"; '
                    "building use: office; building length: 20 m; building width: "
                    "10 m; floor-to-floor height: 3 m; story count: 2; zone layout: "
                    "single zone; window-to-wall ratio (WWR): 0.4; heating setpoint: "
                    "20 °C; cooling setpoint: 26 °C. Apply system defaults to "
                    "unspecified fields."
                ),
            },
        )
        self.assertEqual(
            tuple(record.family.value for record in records),
            ("zh_concise", "zh_expert", "en_concise", "en_expert"),
        )
        self.assertTrue(
            all(
                record.prompt_config_sha256
                == prompts.prompt_config_sha256(config)
                for record in records
            )
        )

    def test_custom_disclosure_never_leaks_defaulted_facts(self) -> None:
        """渲染器读取 ResolvedSpec 未披露数值时本测试必须失败。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        plan = DisclosurePlan(frozenset({"building_name", "length"}))
        record = prompts.render_clean_prompt(
            self._spec(),
            plan,
            prompts.PromptFamily.ZH_CONCISE,
            config,
        )

        self.assertEqual(
            record.prompt,
            "请生成一栋名称为“Demo”、长20 m的建筑模型；其余参数使用系统默认值。",
        )
        self.assertEqual(
            record.scenario_spec_draft_target.length.status,
            FieldStatus.REQUESTED,
        )
        self.assertEqual(
            record.scenario_spec_draft_target.width.status,
            FieldStatus.DEFAULTED,
        )
        self.assertNotIn("10", record.prompt)
        self.assertNotIn("办公", record.prompt)

    def test_rendering_is_deterministic_and_records_family_metadata(self) -> None:
        """同输入产生不同文本、顺序或元数据时确定性断言必须失败。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        first = prompts.render_all_clean_prompts(self._spec(), config)
        second = prompts.render_all_clean_prompts(self._spec(), config)

        self.assertEqual(first, second)
        self.assertEqual(first[0].language, prompts.PromptLanguage.ZH)
        self.assertEqual(first[0].style, prompts.PromptStyle.CONCISE)
        self.assertEqual(first[-1].language, prompts.PromptLanguage.EN)
        self.assertEqual(first[-1].style, prompts.PromptStyle.EXPERT)

    def test_record_carries_compatible_draft_schema_version(self) -> None:
        """遗漏 Draft 版本时记录不得伪装成完整的版本化追溯对象。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        record = prompts.render_all_clean_prompts(self._spec(), config)[0]

        self.assertEqual(
            record.model_dump(mode="json").get("draft_schema_version"),
            "0.1",
        )
        self.assertEqual(
            record.scenario_spec_draft_target.schema_version,
            config.draft_schema_version,
        )

    def test_unknown_disclosure_field_fails_before_rendering(self) -> None:
        """拼错字段名不得被静默忽略并产生不可标定 Prompt。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        plan = DisclosurePlan(frozenset({"building_nmae"}))

        with self.assertRaises(ConfigurationError) as context:
            prompts.render_clean_prompt(
                self._spec(),
                plan,
                prompts.PromptFamily.EN_CONCISE,
                config,
            )

        self.assertEqual(
            context.exception.context["unknown_fields"],
            ["building_nmae"],
        )

    def test_unsafe_building_name_is_rejected_before_interpolation(self) -> None:
        """名称中的模板分隔符或换行不得产生歧义 Prompt。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)
        unsafe_spec = self._spec().model_copy(
            update={"building_name": 'A\nB；C"D'}
        )
        plan = DisclosurePlan(frozenset({"building_name"}))

        with self.assertRaises(ConfigurationError) as context:
            prompts.render_clean_prompt(
                unsafe_spec,
                plan,
                prompts.PromptFamily.ZH_EXPERT,
                config,
            )

        self.assertEqual(context.exception.context["building_name"], 'A\nB；C"D')

    def test_empty_disclosure_plan_is_rejected(self) -> None:
        """零披露计划不得生成缺少建筑事实的畸形 Prompt。"""

        config = prompts.load_prompt_config(PROMPT_CONFIG_PATH)

        with self.assertRaises(ConfigurationError) as context:
            prompts.render_clean_prompt(
                self._spec(),
                DisclosurePlan(frozenset()),
                prompts.PromptFamily.ZH_CONCISE,
                config,
            )

        self.assertEqual(context.exception.context["requested_fields"], [])


if __name__ == "__main__":
    unittest.main()
