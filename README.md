# Video Cover Reference Skill

一个可复用的 Codex Skill：输入人物照片和准确标题，生成 9:16 短视频封面，并在三套参考视觉之间路由：

- 黄橙米白撕纸拼贴
- 宝蓝薄荷绿撕纸拼贴
- 黄黑写实办公演示

Skill 会保留真人照片的脸部、发丝、服装、手势和产品透视，并把标题放在指定的留白区域。中文标题先做逐字检查；如果图像模型返回错字，再进入后处理。

## 在 Codex 中使用

把这个仓库放到个人 Skills 目录：

```bash
cp -R video-cover-reference "$HOME/.codex/skills/video-cover-reference"
```

也可以直接把仓库目录交给 Codex 的 Skill 安装流程。

调用时提供：

```text
使用 $video-cover-reference
照片：上传一张人物照片
标题：你的准确标题
画幅：默认 9:16
```

## 命令行生成

脚本使用兼容 OpenAI Responses API 的 `image_generation` 接口，并支持多张图片输入。环境变量只在本机设置，不要写进仓库：

```bash
export IMAGE_API_KEY="..."
export IMAGE_API_BASE_URL="https://your-compatible-provider.example/v1"
export IMAGE_HOST_MODEL="your-host-model"

python3 scripts/generate_with_references.py \
  --prompt-file /absolute/path/prompt.txt \
  --input-image /absolute/path/person.jpg \
  --input-image /absolute/path/style-reference.png \
  --output /absolute/path/cover.png \
  --size 1152x2048 \
  --quality high
```

`IMAGE_API_BASE_URL` 默认是 `https://api.openai.com/v1`，但具体模型是否可用取决于你的服务商账号和路由。`IMAGE_API_KEY` 优先，也兼容 `OPENAI_API_KEY`。脚本不会打印密钥。

## 目录

- `SKILL.md`：Skill 入口和工作流
- `references/`：视觉系统、提示词模板、验收清单
- `assets/`：用户提供的风格参考图
- `scripts/generate_with_references.py`：带图片输入的生成脚本
- `.env.example`：环境变量名称示例，不含真实凭据

## 隐私说明

`assets/` 包含真人参考封面，因此默认建议把仓库设为 **Private**。如果要公开仓库，请先移除或替换带有真人脸部的参考图，再把 `SKILL.md` 中对本地参考图的依赖改为用户自己的输入图。

## 许可

仓库中的 Skill 文本和脚本使用 MIT License。参考图片仍属于提供者，不因仓库许可而转让肖像权或图片权利。
