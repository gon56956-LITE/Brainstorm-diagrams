---
diagram_type: fmea_table
fmea_type: process
language: zh
---

# 客户现场间歇性通信中断 FMEA

Goal: 识别影响客户恢复和根因定位的主要失效模式，并明确控制与行动。
Project: 光模块客户现场试运行问题
Owner: 质量工程
Review Frequency: 每周
Note: 每行聚焦一个失效模式。

## Row F1

Item / Function: 固件错误恢复
Failure Mode: 错误恢复机制异常
Effects:
- 链路中断后恢复时间过长
- 客户验证进度受阻
Causes:
- 状态机边界条件覆盖不足
- 错误恢复计时配置不一致
Prevention Controls:
- 固件发布评审
- 版本冻结流程
Detection Controls:
- 客户日志解析
- 长时间链路稳定性测试
Severity: 8
Occurrence: 5
Detection: 6
Recommended Actions:
- 补充状态机边界条件测试
- 增加回归用例
Owner: 固件团队
Target Completion: 2026-06-14
Status: 进行中

## Row F2

Item / Function: 现场配置确认
Failure Mode: 主机配置或速率参数不匹配
Effects:
- 链路协商失败
- 间歇性掉线
Causes:
- 客户现场配置与发布要求不一致
- 速率自协商参数未锁定
Prevention Controls:
- 发布配置矩阵
- 应用工程检查清单
Detection Controls:
- 现场配置核对
- 模块固件版本确认
Severity: 8
Occurrence: 4
Detection: 3
Recommended Actions:
- 与客户完成配置复核
- 发布临时规避设置
Owner: 应用工程团队
Target Completion: 2026-06-07
Status: 开放

## Row F3

Item / Function: 高速信号链路
Failure Mode: 信号完整性裕量不足
Effects:
- 误码率升高
- 眼图裕量降低
- 链路间歇性中断
Causes:
- 主机板连接器损耗偏高
- 抖动裕量不足
- 模块端均衡设置不合适
Prevention Controls:
- 设计评审
- 参考主机验证
Detection Controls:
- 眼图测试
- 误码率测试
- 温度条件下链路测试
Severity: 9
Occurrence: 3
Detection: 6
Recommended Actions:
- 进行复现实验
- 完成 SI 裕量评估
Owner: 硬件团队
Target Completion: 2026-06-21
Status: 计划中

## Row F4

Item / Function: 现场证据收集
Failure Mode: 日志和告警记录不完整
Effects:
- 问题定位时间变长
- 跨团队判断不一致
Causes:
- 客户系统日志保存时间短
- 现场事件时间点未统一记录
Prevention Controls:
- 客户问题受理流程
- 日志收集模板
Detection Controls:
- 应用工程师现场同步
- 问题追踪表
Severity: 5
Occurrence: 6
Detection: 2
Recommended Actions:
- 更新日志收集模板
- 更新问题追踪表
Owner: 质量团队
Target Completion: 2026-06-05
Status: 完成

## Row F5

Item / Function: 留样复测
Failure Mode: 复测未覆盖现场条件
Effects:
- 内部无法复现客户中断
- 根因判断延迟
Causes:
- 复测使用不同主机
- 温度条件和链路参数不同
Prevention Controls:
- 标准复测流程
- 样品留存规则
Detection Controls:
- 复测报告审核
- 条件比对
Severity: 7
Occurrence: 4
Detection: 5
Recommended Actions:
- 建立客户等效复测配置
Owner: 测试团队
Target Completion: 2026-06-12
Status: 进行中
