# Video Cover Reference Skill

一个可复用的 Codex Skill：输入人物照片和准确标题，生成 9:16 短视频封面，并在三套参考视觉之间路由：

- 黄橙米白撕纸拼贴
- 宝蓝薄荷绿撕纸拼贴
- 黄黑写实办公演示

工作流要求保留人物身份、服装、手势和照片的真实立体感，按指定位置排标题，再检查中文、手部与尺寸。生成效果取决于输入照片和所用模型，必要时需要修图或校字。

这是可安装的工作流和提示词，不是独立生图网站，也不附带 API 额度。日常使用可以简化成“照片＋标题”，首次需要安装并准备可用的图片生成能力。

## 示例：我的照片 → 我的封面

<table>
  <tr>
    <td><img src="assets/examples/user-photo-reference.jpg" width="240" alt="作者本人照片的公开示例，带水印" /></td>
    <td><img src="assets/examples/user-cover-9x16.jpg" width="240" alt="根据作者照片生成的 9:16 封面示例，带水印" /></td>
  </tr>
  <tr>
    <td>输入照片（缩小处理版）</td>
    <td>输出封面（缩小处理版）</td>
  </tr>
</table>

示例图用于说明工作流效果，不是可自由再利用的素材。原始高清照片不在仓库中；肖像和图片边界见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。

## 在 Codex 中使用

将仓库链接交给 Codex 的 `$skill-installer`，或在 macOS / Linux 终端运行：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/franklinandina141-design/video-cover-reference-skill.git \
  "$HOME/.agents/skills/video-cover-reference"
```

若目标文件夹已存在，先检查已有版本，不要覆盖。也可以下载分享 ZIP，解压后把内含 `SKILL.md` 的 `video-cover-reference` 文件夹放到 `.agents/skills/`。没有 Git 的 Windows 用户可以把它放到 `%USERPROFILE%\.agents\skills\video-cover-reference`。

安装后开启新任务；如果没有识别到 Skill，重启 Codex。安装路径依据 [Codex 官方 Skills 文档](https://developers.openai.com/codex/skills/)。其他 Agent 可参考这套文件结构，但本仓库未逐一测试。

仓库公开后，任何人都可以查看和克隆代码与示例；仓库不包含原始照片、API 密钥或作者的生图额度。示例素材的肖像和图片使用边界见 [ASSET-NOTICE.md](ASSET-NOTICE.md) 和 [assets/README.md](assets/README.md)。

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
- `assets/examples/`：经过缩小、去元数据并加示例水印的公开演示素材
- `scripts/generate_with_references.py`：带图片输入的生成脚本
- `.env.example`：环境变量名称示例，不含真实凭据
- `tests/`：使用本地模拟服务的脚本验证

## 公开示例与肖像保护

可以分享 Skill 文本和脚本。公开示例使用的是作者本人提供的照片和成品的缩小版本，已移除 EXIF 等元数据，并加上“仅作公开示例”的水印；原始高清照片不进入仓库。

代码和文档按 MIT 发布；图片、肖像和其他素材不在 MIT 范围内。图片仅用于查看本 Skill 的示例效果，禁止下载后再发布、出售、制作素材包、训练数据集、做人脸识别、换脸、冒充作者或用于与作者无关的商业宣传。完整声明见 [ASSET-NOTICE.md](ASSET-NOTICE.md)。

这些措施能明确授权范围、减少原图暴露和降低误用风险，但不能阻止 GitHub 用户截图、复制或镜像；如果未来不想继续公开，应删除示例文件并重新检查 Git 历史与镜像。

## 许可

仓库中的 Skill 文本和脚本使用 MIT License。参考图片仍属于提供者，不因仓库许可而转让肖像权或图片权利。
