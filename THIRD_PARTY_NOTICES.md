# Third-party notices

## English

FactoryTrace's original code, Skill instructions, and documentation are licensed under MIT; see [LICENSE](LICENSE). Upstream components keep their own licenses. The root MIT license does not relicense them.

| Included component | Origin | License | Local notice |
|---|---|---|---|
| `eng`, `osd`, `chi_sim`, `chi_tra` Tesseract data | [tesseract-ocr/tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd) | Apache-2.0 | [LICENSE](factory_trace_toolkit/resources/tessdata/LICENSE), [hash manifest](factory_trace_toolkit/resources/tessdata/MANIFEST.json) |
| Noto Sans CJK SC Regular font used to regenerate synthetic OCR probes | [notofonts/noto-cjk](https://github.com/notofonts/noto-cjk/tree/f8d157532fbfaeda587e826d4cd5b21a49186f7c) | SIL Open Font License 1.1 | [LICENSE](factory_trace_toolkit/resources/fonts/LICENSE), [hash manifest](factory_trace_toolkit/resources/fonts/MANIFEST.json) |

The probe PNGs contain only synthetic OCR test text, not photographs of real products, labels, facilities, staff, customers, or documents. Their source font is included so maintainers need not depend on a proprietary system font.

Python dependencies are installed by the user; their source and binary distributions are not vendored here. FFmpeg, Tesseract, and ExifTool executables are not bundled. Each external package or executable retains its upstream license and platform-specific terms. Review those terms before redistributing executable environments.

README design references are acknowledged in [README style research](docs/README_STYLE_RESEARCH.md). Only structural ideas are adapted; third-party marketing claims, screenshots, logos, and source code are not copied into this project.

## 中文

FactoryTrace 自有代码、Skill 指令与文档采用 MIT，见 [LICENSE](LICENSE)。第三方组件保留自己的许可，根目录 MIT 不覆盖或重新授权这些组件。

| 随包组件 | 来源 | 许可 | 本地记录 |
|---|---|---|---|
| Tesseract 英文、方向检测、简中、繁中语言数据 | [tessdata_fast 固定版本](https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd) | Apache-2.0 | [许可](factory_trace_toolkit/resources/tessdata/LICENSE)、[哈希清单](factory_trace_toolkit/resources/tessdata/MANIFEST.json) |
| 用于重新生成合成 OCR 探针的 Noto CJK SC 字体 | [noto-cjk 固定版本](https://github.com/notofonts/noto-cjk/tree/f8d157532fbfaeda587e826d4cd5b21a49186f7c) | SIL Open Font License 1.1 | [许可](factory_trace_toolkit/resources/fonts/LICENSE)、[哈希清单](factory_trace_toolkit/resources/fonts/MANIFEST.json) |

探针 PNG 只有虚构的 OCR 测试文字，不包含真实产品、标签、厂房、员工、客户或文件照片。随包提供开源字体，使维护者不依赖私有系统字体即可再生探针。

Python 依赖由用户安装，本仓库不复制其源码或二进制发行包，也不捆绑 FFmpeg、Tesseract、ExifTool 可执行文件。第三方安装物继续适用各自的许可和平台条款；分发完整可执行环境前应另行核对。

README 排版来源记录在 [README 格式研究](docs/README_STYLE_RESEARCH.md)。这里只借鉴结构，不复制第三方宣传断言、截图、商标或源代码。
