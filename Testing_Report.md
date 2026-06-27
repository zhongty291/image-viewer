# 测试报告（Testing Report）

## 测试环境

| 项目 | 说明 |
|------|------|
| 操作系统 | Windows 11 x64 |
| Python 版本 | 3.12.6 |
| 测试框架 | pytest 9.1.1 |
| 测试日期 | 2026-06-28 |

## TDD 实践概述

本项目采用 **TDD（测试驱动开发）** 方法开发，遵循 **Red-Green-Refactor** 三阶段循环：

1. **红灯（Red）**：先编写测试用例，运行测试确认失败（功能尚未实现）
2. **绿灯（Green）**：编写最小实现代码使测试通过
3. **重构（Refactor）**：优化代码结构，保持测试通过

### 测试开发顺序
```
test_model.py (编写) → model.py (实现) → test_controller.py (编写) → controller.py (实现)
```

## 测试用例列表

### 一、Model 层测试（test_model.py）— 20 个用例

#### 1.1 图片加载测试（TestImageLoading）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T01 | test_load_png_success | 成功加载 PNG 图片并返回正确的元信息 | ✅ PASS |
| T02 | test_load_jpg_success | 成功加载 JPG 图片 | ✅ PASS |
| T03 | test_load_nonexistent_file | 加载不存在的文件应抛出 FileNotFoundError | ✅ PASS |
| T04 | test_load_unsupported_format | 加载不支持的文件格式应抛出 ValueError | ✅ PASS |
| T05 | test_is_supported_static_method | 静态方法 is_supported 正确判断文件格式 | ✅ PASS |

#### 1.2 旋转测试（TestRotation）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T06 | test_rotate_cw_changes_rotation_angle | 顺时针旋转后角度更新为 90 | ✅ PASS |
| T07 | test_rotate_ccw_changes_rotation_angle | 逆时针旋转后角度更新为 270 | ✅ PASS |
| T08 | test_rotate_180_changes_rotation_angle | 180°旋转后角度更新为 180 | ✅ PASS |
| T09 | test_four_rotations_return_to_zero | 4 次顺时针旋转后角度归零 | ✅ PASS |
| T10 | test_rotation_swaps_dimensions | 旋转 90°后宽高互换 | ✅ PASS |
| T11 | test_reload_original_resets_rotation | reload_original 后旋转角度归零 | ✅ PASS |
| T12 | test_rotate_without_loaded_image | 未加载图片时旋转操作安全返回 | ✅ PASS |

#### 1.3 缩放计算测试（TestZoomCalculation）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T13 | test_fit_scale_wider_image | 宽图片按宽度限制计算缩放比 | ✅ PASS |
| T14 | test_fit_scale_taller_viewport | 高视口按高度限制计算缩放比 | ✅ PASS |
| T15 | test_fit_scale_no_image | 未加载图片返回默认 1.0 | ✅ PASS |
| T16 | test_fit_scale_exact_fit | 视口与图片一致时缩放比 1.0 | ✅ PASS |

#### 1.4 信息提取测试（TestImageInfo）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T17 | test_get_info_returns_imageinfo | get_info 返回正确的 ImageInfo 对象 | ✅ PASS |
| T18 | test_get_info_before_load | 未加载时返回空 ImageInfo | ✅ PASS |
| T19 | test_info_file_size_format | 文件大小格式含单位标识 | ✅ PASS |
| T20 | test_filepath_property | filepath 属性返回正确路径 | ✅ PASS |

### 二、Controller 层测试（test_controller.py）— 16 个用例

#### 2.1 缩放控制测试（TestZoomControl）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T21 | test_zoom_in_increases_scale | 放大后比例增大 | ✅ PASS |
| T22 | test_zoom_out_decreases_scale | 缩小后比例减小 | ✅ PASS |
| T23 | test_zoom_in_respects_max | 放大不超过 500% 上限 | ✅ PASS |
| T24 | test_zoom_out_respects_min | 缩小不低于 10% 下限 | ✅ PASS |
| T25 | test_zoom_to_clamps_value | 非法值被钳制到有效范围 | ✅ PASS |
| T26 | test_zoom_100_sets_scale_to_one | 100% 缩放到 1.0 | ✅ PASS |
| T27 | test_zoom_fit_calculates_fit_scale | 适配窗口调用 Model 计算 | ✅ PASS |

#### 2.2 旋转控制测试（TestRotationControl）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T28 | test_rotate_cw_updates_model | Controller 委托 Model 旋转 90° | ✅ PASS |
| T29 | test_rotate_ccw_updates_model | Controller 委托 Model 旋转 270° | ✅ PASS |
| T30 | test_rotate_180_updates_model | Controller 委托 Model 旋转 180° | ✅ PASS |
| T31 | test_reset_rotation | 重置旋转角度归零 | ✅ PASS |

#### 2.3 导航测试（TestNavigation）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T32 | test_build_file_list | 打开图片后自动建立导航列表 | ✅ PASS |
| T33 | test_navigate_next | 切换到下一张图片 | ✅ PASS |
| T34 | test_navigate_prev | 切换到上一张图片（循环） | ✅ PASS |

#### 2.4 平移测试（TestPanOffset）

| 编号 | 测试方法 | 测试内容 | 结果 |
|------|---------|---------|------|
| T35 | test_update_pan_accumulates | 多次平移偏移量正确累加 | ✅ PASS |
| T36 | test_reset_pan_zeros_offset | reset_pan 将偏移归零 | ✅ PASS |

## 测试结果汇总

```
============================= test session starts =============================
collected 36 items

tests/test_controller.py::TestZoomControl::test_zoom_in_increases_scale PASSED
tests/test_controller.py::TestZoomControl::test_zoom_out_decreases_scale PASSED
tests/test_controller.py::TestZoomControl::test_zoom_in_respects_max PASSED
tests/test_controller.py::TestZoomControl::test_zoom_out_respects_min PASSED
tests/test_controller.py::TestZoomControl::test_zoom_to_clamps_value PASSED
tests/test_controller.py::TestZoomControl::test_zoom_100_sets_scale_to_one PASSED
tests/test_controller.py::TestZoomControl::test_zoom_fit_calculates_fit_scale PASSED
tests/test_controller.py::TestRotationControl::test_rotate_cw_updates_model PASSED
tests/test_controller.py::TestRotationControl::test_rotate_ccw_updates_model PASSED
tests/test_controller.py::TestRotationControl::test_rotate_180_updates_model PASSED
tests/test_controller.py::TestRotationControl::test_reset_rotation PASSED
tests/test_controller.py::TestNavigation::test_build_file_list PASSED
tests/test_controller.py::TestNavigation::test_navigate_next PASSED
tests/test_controller.py::TestNavigation::test_navigate_prev PASSED
tests/test_controller.py::TestPanOffset::test_update_pan_accumulates PASSED
tests/test_controller.py::TestPanOffset::test_reset_pan_zeros_offset PASSED
tests/test_model.py::TestImageLoading::test_load_png_success PASSED
tests/test_model.py::TestImageLoading::test_load_jpg_success PASSED
tests/test_model.py::TestImageLoading::test_load_nonexistent_file PASSED
tests/test_model.py::TestImageLoading::test_load_unsupported_format PASSED
tests/test_model.py::TestImageLoading::test_is_supported_static_method PASSED
tests/test_model.py::TestRotation::test_rotate_cw_changes_rotation_angle PASSED
tests/test_model.py::TestRotation::test_rotate_ccw_changes_rotation_angle PASSED
tests/test_model.py::TestRotation::test_rotate_180_changes_rotation_angle PASSED
tests/test_model.py::TestRotation::test_four_rotations_return_to_zero PASSED
tests/test_model.py::TestRotation::test_rotation_swaps_dimensions PASSED
tests/test_model.py::TestRotation::test_reload_original_resets_rotation PASSED
tests/test_model.py::TestRotation::test_rotate_without_loaded_image PASSED
tests/test_model.py::TestZoomCalculation::test_fit_scale_wider_image PASSED
tests/test_model.py::TestZoomCalculation::test_fit_scale_taller_viewport PASSED
tests/test_model.py::TestZoomCalculation::test_fit_scale_no_image PASSED
tests/test_model.py::TestZoomCalculation::test_fit_scale_exact_fit PASSED
tests/test_model.py::TestImageInfo::test_get_info_returns_imageinfo PASSED
tests/test_model.py::TestImageInfo::test_get_info_before_load PASSED
tests/test_model.py::TestImageInfo::test_info_file_size_format PASSED
tests/test_model.py::TestImageInfo::test_filepath_property PASSED

============================= 36 passed in 0.16s ==============================
```

| 统计项 | 数值 |
|--------|------|
| 测试总数 | 36 |
| 通过 | 36 |
| 失败 | 0 |
| 通过率 | 100% |
| 执行耗时 | 0.16s |

## TDD 实践效果分析

### 实践体会
1. **测试先行迫使清晰思考**：在编写代码之前，必须先明确方法的输入、输出和边界情况，这自然地引导出更好的接口设计。
2. **回归安全网**：在后续添加旋转重置、缩放边界等功能时，已有的 36 个测试用例立即验证了新修改是否破坏了原有功能。
3. **文档价值**：测试用例本身就是最好的代码文档——其他开发者可以通过阅读测试代码快速理解每个方法的行为预期。

### 测试覆盖的关键场景
- ✅ 正常路径：成功加载图片、正常缩放、旋转操作
- ✅ 异常路径：文件不存在、格式不支持
- ✅ 边界值：缩放最小值 10%、最大值 500%、空值处理
- ✅ 状态累积：多次旋转叠加、拖拽偏移累加
- ✅ 资源清理：reload_original 恢复初始状态

### 集成测试（手动验证）
除自动化的单元测试外，进行了以下手动集成测试：
1. 启动应用 → 打开 JPG 图片 → 鼠标滚轮缩放正常
2. 顺时针旋转 90°×4 → 图片回到原始方向
3. 打开含多张图片的目录 → 左右键切换正常
4. 放大到 500% 后拖拽平移 → 图片平滑移动
5. 信息面板正确显示分辨率、格式、文件大小
