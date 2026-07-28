# Godot AI DevKit

一套可以直接放进 Godot 项目、交给 AI 阅读的开发能力包。它把 Gvtt 长期开发中可跨项目复用的产品判断、开发要求、错误经验、Godot 代码规范、基础细分 Skill（技能）和 Godot 4.7 离线文档整理在一起。

它不依赖 Codex、Claude、Gemini 或其他特定 AI，也不是安装器、Godot 插件或运行工具。

## 里面有什么

```text
godot-ai-devkit/
├── README.md
├── SKILL.md
├── AGENTS.template.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── references/
│   ├── product_first.md
│   ├── reuse_first.md
│   ├── godot_code_style.md
│   ├── workflow.md
│   ├── verification.md
│   ├── debugging.md
│   └── godot-4.7-docs/       Godot 4.7 英文离线文档
└── skills/
    ├── godot-project-start/
    ├── godot-gdscript/
    ├── godot-scene-data/
    ├── godot-ui-input/
    ├── godot-debugging/
    ├── godot-testing/
    ├── godot-code-review/
    ├── godot-2d/
    └── godot-3d/
```

- 根 `SKILL.md` 是总入口，负责产品判断、现成方案优先、最小实现、验证和日志。
- `skills/` 是按任务读取的基础 Godot 技能，不让无关领域占用 AI 上下文。
- `references/` 保存开发要求、代码规范、错误经验和精确版本文档。
- `AGENTS.template.md` 用于形成新项目自己的长期规则。

## 新项目最短用法

1. 把整个 `godot-ai-devkit` 文件夹放入 Godot 项目根目录。
2. 复制 `AGENTS.template.md` 为项目根目录的 `AGENTS.md`，填写项目定位、目标玩家、核心体验、不做范围、平台和 Godot 精确版本。
3. 对 AI 说：

   > 先完整读取 `godot-ai-devkit/SKILL.md` 和项目根目录 `AGENTS.md`。根据当前任务读取 `SKILL.md` 指定的细分技能；本项目使用 Godot 4.7 时，不确定 API 必须搜索随包离线文档。检查现有项目后再开始，不要覆盖已有规则。

不支持 Skill（技能）自动发现的 AI 也能把这些文件当普通指令读取。支持技能目录的 AI 可以把根技能和需要的 `skills/*` 分别安装到自己的技能目录，但这不是使用本包的前提。

## 能继承什么

- 从玩家或用户真实目标出发，避免把简单功能做成复杂系统和多余界面；
- 主动寻找项目现有实现、Godot 官方能力、插件和开源方案；
- Godot 4 的版本安全、代码、场景、数据、界面和输入规范；
- 调试、自动测试、运行态、原生窗口和用户产品验收的边界；
- Gvtt 中已经证明能跨项目复用的失败模式和防错方法；
- Godot 4.7 API（应用程序接口）与手册的离线查询能力。

## 不能替项目决定什么

本包不会自动知道新游戏的玩法、目标用户、数据结构、已选插件和历史决定，也不会把 Gvtt 的 CPR（《赛博朋克 RED》）规则、地图架构或测试直接搬进其他项目。新项目仍要完成 `AGENTS.md` 的项目定位，并为自己的功能编写自己的自动测试。

随包离线文档只对应 Godot 4.7。项目版本不一致时，不能用它证明该版本的 API；应改用目标精确版本的官方文档。

## 许可证

本包原创内容使用 MIT License（MIT 许可证）。`references/godot-4.7-docs/` 中的 Godot 文档使用 CC BY 3.0（知识共享署名 3.0），详见 `THIRD_PARTY_NOTICES.md`。
