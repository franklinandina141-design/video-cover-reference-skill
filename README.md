# Video Cover Reference Skill

一个可复用的 Codex Skill：输入人物照片和准确标题，生成 9:16 短视频封面，并在三套参考视觉之间路由：

- 黄橙米白撕纸拼贴
- 宝蓝薄荷绿撕纸拼贴
- 黄黑写实办公演示

工作流要求保留人物身份、服装、手势和照片的真实立体感，按指定位置排标题，再检查中文、手部与尺寸。生成效果取决于输入照片和所用模型，必要时需要修图或校字。

这是可安装的工作流和提示词，不是独立生图网站，也不附带 API 额度。日常使用可以简化成“照片＋标题”，首次需要安装并准备可用的图片生成能力。

## 在 Codex 中使用

将仓库链接交给 Codex 的 `$skill-installer`，或在 macOS / Linux 终端运行：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/franklinandina141-design/video-cover-reference-skill.git \
  "$HOME/.agents/skills/video-cover-reference"
```

若目标文件夹已存在，先检查已有版本，不要覆盖。也可以下载分享 ZIP，解压后把内含 `SKILL.md` 的 `video-cover-reference` 文件夹放到 `.agents/skills/`。没有 Git 的 Windows 用户可以把它放到 `%USERPROFILE%\.agents\skills\video-cover-reference`。

安装后开启新任务；如果没有识别到 Skill，重启 Codex。安装路径依据 [Codex 官方 Skills 文档](https://developers.openai.com/codex/skills/)。其他 Agent 可参考这套文件结构，但本仓库未逐一测试。

仓库当前为私有时，只有拥有访问权限的 GitHub 用户能克隆；ZIP 可直接分发。面向所有观众分享仓库链接前，应确认仓库已公开。

调用时提供：

```text
使用 $video-cover-reference
照片：上传一张人物照片
标题：你的准确标题
画幅：默认 9:16
补充要求：标题放在手部上方
```

可以指定“黄橙拼贴”“蓝绿拼贴”或“黄黑办公”；不指定时由 Skill 结合照片和主题选择。参考图中的人脸只用于观察构图，不作为新封面的人物身份来源。

## 图片生成能力

- 已有支持图片编辑的工具：按 Skill 加载照片和风格参考图，不需要额外安装作者本机的 `image25-sunburst` Skill。
- 使用下方脚本：需要 Python 3，以及支持 Responses `image_generation` 工具、图片输入和 SSE 输出的服务。服务商需要同时提供可用的 host model 与 image model。
- 没有图片生成能力时，可以使用提示词模板，但仅安装 Skill 不会新增图片模型或额度。

作者原始封面已通过自己配置的 Image 2.5 路由实测。`gpt-image-2.5-sunburst` 是该配置使用的模型名称，不代表每个服务商或官方 API 都支持它。分享版不内置服务地址或模型别名；不要把某个服务商的密钥发给另一个服务商。

## 命令行生成

在安装目录执行。先从 `references/prompt-template.md` 整理一份提示词，保存为本地文本，再设置同一个服务商提供的配置（以下值需替换；`.env` 不会被脚本自动加载）：

```bash
export IMAGE_API_KEY="..."
export IMAGE_API_BASE_URL="https://your-compatible-provider.example/v1"
export IMAGE_HOST_MODEL="your-host-model"
export IMAGE_MODEL="your-image-model"

python3 scripts/generate_with_references.py \
  --prompt-file /absolute/path/prompt.txt \
  --input-image /absolute/path/person.jpg \
  --input-image /absolute/path/style-reference.png \
  --output /absolute/path/cover.png \
  --size auto \
  --quality high
```

`IMAGE_API_BASE_URL` 填以 `/v1` 结尾的基础地址，不加 `/responses`。脚本没有服务地址和模型默认值；缺配置时会直接提示。`IMAGE_API_KEY` 优先，也兼容 `OPENAI_API_KEY`。

画幅写进提示词；若服务商支持明确尺寸，可替换 `--size auto`。脚本只保存模型返回的 PNG，不会自动修正比例、校字或修手；这些属于 Skill 的后续验收步骤。最终尺寸应实际读取，不能只看请求参数。生图费用、速度、模型权限以服务商为准。

脚本不会覆盖同名文件，不会自动切换模型或重试收费请求。出错后先查看服务端任务状态，再决定是否重试。

## 验证范围

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/generate_with_references.py
```

测试使用本地模拟服务检查图片传入、环境配置、错误处理和文件保存，不消耗生图额度。分享版尚未对每个服务商进行真实生图测试；原始案例成功不代表所有新配置都已验证。

## 目录

- `SKILL.md`：Skill 入口和工作流
- `references/`：视觉系统、提示词模板、验收清单
- `assets/`：用户提供的风格参考图
- `scripts/generate_with_references.py`：带图片输入的生成脚本
- `.env.example`：环境变量名称示例，不含真实凭据
- `tests/`：使用本地模拟服务的脚本验证

## 参考图与分享

可以分享 Skill 文本和脚本。`assets/` 中的真人参考封面用于视觉示例，有相应分享权利的照片可以保留；是否公开不由“出现真人”这一点单独决定。图片不自动适用 MIT 许可，另作传播或商业使用时应取得相应授权。输出应使用使用者提供的人物照片，不复用参考图人物冒充使用者。

## 许可

仓库中的 Skill 文本和脚本使用 MIT License。参考图片仍属于提供者，不因仓库许可而转让肖像权或图片权利。
