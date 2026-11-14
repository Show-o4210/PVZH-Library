# ThePrimalPea 翻译贡献与接入状态

本包明确保留 [ThePrimalPea / The Primal Pea](https://github.com/ThePrimalPea) 的署名，未把其文案算作整理者原创。以下基于当前 main 可达历史与 GitHub 作者身份核对，不含未合并分支或尚未提交的工作。

## 本地化词条

5 个提交共 94 个不同语言／键的修订，已逐条纳入 [corrections.json](corrections.json)，保留作者、提交、修改前后值、R44/R64 状态。与原有 39 条无键冲突；原有 FIX 编号未改变。当前共 **133 条**交接记录。

这些修订涵盖越南语牌组术语、宝石/卡包名称、英雄计数说明，以及中英越项目名称和英文大小写。部分是术语与风格选择，不应笼统称为“94 个错误”。**94 条均已存在于当前 R64 仓库词表，不等于 APK 已生效；不应再次对 R64 机械应用同一补丁。**

| 提交 | 文件/范围 | 词条数 |
| --- | --- | --- |
| [911cb19](https://github.com/Show-o4210/PvZH-AML/commit/911cb19f443bf9e739f5f9884dd9876208b57308) | `pvzh-launcher/i18n/r-2-64/vi-VN/floating-tools/floating-deck.json` | 51 |
| [9575dc6](https://github.com/Show-o4210/PvZH-AML/commit/9575dc69f56a32483e7d02a80c9cb0991ca448a5) | `pvzh-launcher/i18n/r-2-64/vi-VN/floating-tools/floating-resources.json` | 27 |
| [b7aa331](https://github.com/Show-o4210/PvZH-AML/commit/b7aa33194629022199a5addc762ce0d0bb031b34) | `pvzh-launcher/i18n/r-2-64/en-US/floating-tools/floating-resources.json` | 7 |
| [28bc01e](https://github.com/Show-o4210/PvZH-AML/commit/28bc01ed3e0291139762befb596d27380732abfa) | `pvzh-launcher/i18n/r-2-64/en-US/floating-tools/floating-resources.json` | 7 |
| [1c862f1](https://github.com/Show-o4210/PvZH-AML/commit/1c862f164328b232da9ca7d74f52b7475b1f39aa) | `pvzh-launcher/i18n/r-2-64/zh-CN/floating-tools/floating-resources.json` | 2 |

R44 对照：49 条已同文，45 条值不同，0 条无对应键。R44 只是版本对照，不是要求回写旧版本。

### 必须人工复核的一项

`overlay.deck.import.description`（vi-VN，`911cb19`）把编码前缀 `PVZH1` 写成 `PvZH1`。本包保留作者原文作证据，并标记 `requires-protocol-prefix-review`，**不要自动采用该大小写变化**。应以解析器认可的协议标记为准；其他提示仍使用 `PVZH1`。这不是已经证实的运行 bug，也不能因为品牌写法是 PvZH 就改协议名。

越南语 `bộ bài`/`bộ thẻ`、Plant/Cây 等用词仍有邻近条目不一致，后续按项目术语表统一，不把未修改的相邻字符串冒认为该作者修订。

## 文档贡献（18 个提交）

这些提交已在仓库文档历史中，不是 APK 字符串。保留完整来源与涉及路径，供文档维护时追踪；**不把 README 改名/导航操作当作运行翻译补丁重放**。机器清单见 [contributor-commits.json](contributor-commits.json)。

| 提交 | 说明 | 涉及路径 |
| --- | --- | --- |
| [1c455f9](https://github.com/Show-o4210/PvZH-AML/commit/1c455f9a4561973bec954c24615324f5c3a06f01) | Update CN README.md | `README.md` |
| [a02712d](https://github.com/Show-o4210/PvZH-AML/commit/a02712db4e72c5d8584612a0cc4a47ec6db8dbb5) | Update CN README.md | `README.md` |
| [973cc8f](https://github.com/Show-o4210/PvZH-AML/commit/973cc8fe24507fe11fbe9ccc046f2996d063d3ec) | Update README.en.md | `README.en.md` |
| [8070d50](https://github.com/Show-o4210/PvZH-AML/commit/8070d506ee0ec60dc8f100f82e6482f176d9a8a4) | Update README.en.md | `README.en.md` |
| [b108b3a](https://github.com/Show-o4210/PvZH-AML/commit/b108b3a394f29b5a4a038df66e3656d2e5bbf64f) | Update README.en.md | `README.en.md` |
| [cd5e133](https://github.com/Show-o4210/PvZH-AML/commit/cd5e133d8e2869816fa91f92a8a1b6c4eab8c57a) | Update README_zh.md | `README.md` |
| [684df97](https://github.com/Show-o4210/PvZH-AML/commit/684df97a21c9c6bd5fb5dc90130e2e5b40b3e962) | Update README.vi.md | `README.vi.md` |
| [35e840e](https://github.com/Show-o4210/PvZH-AML/commit/35e840e8b1885a7be7cf0f5cf3161f8fa2c7a00c) | Update README.vi.md | `README.vi.md` |
| [e6a6bfc](https://github.com/Show-o4210/PvZH-AML/commit/e6a6bfc8f9f3fa7e7b0d434d39f23df76e4ff36d) | Update README.en.md | `README.en.md` |
| [91d4f73](https://github.com/Show-o4210/PvZH-AML/commit/91d4f731f97618646168436fbb1ee2022e3de48d) | Update README.md | `pvzh-launcher/README.md` |
| [d6d2416](https://github.com/Show-o4210/PvZH-AML/commit/d6d2416128018740ad9ca7be5fc6e13eccfe7119) | Update README.en.md | `README.en.md` |
| [9a17cbf](https://github.com/Show-o4210/PvZH-AML/commit/9a17cbf256d3514c2b5ff7102bedacef4e9dafda) | Rename README.md to README_zh_CN.md | `README.md` · `README_zh_CN.md` |
| [7f73dd3](https://github.com/Show-o4210/PvZH-AML/commit/7f73dd31bb50d651a65f40092aff10e9ec3dfdf9) | Update and rename README.en.md to README.md | `README.en.md` · `README.md` |
| [b69531d](https://github.com/Show-o4210/PvZH-AML/commit/b69531d484de09bed357552d0ab1107dbacf0cf0) | Update README_zh_CN.md | `README_zh_CN.md` |
| [49519aa](https://github.com/Show-o4210/PvZH-AML/commit/49519aa3dfe84608f3d3e3a2d9b68c19615e197f) | Update and rename README.vi.md to README.vi_VN.md | `README.vi.md` · `README.vi_VN.md` |
| [cd5df70](https://github.com/Show-o4210/PvZH-AML/commit/cd5df705252a9922e2c7aa6e9f3329dc2960bc62) | Update README.md | `README.md` |
| [e218fa2](https://github.com/Show-o4210/PvZH-AML/commit/e218fa20f2abf45cea80e667fd2a1bbb09a00242) | Rename README.vi_VN.md to README_vi_VN.md | `README.vi_VN.md` · `README_vi_VN.md` |
| [2f4695e](https://github.com/Show-o4210/PvZH-AML/commit/2f4695e8d91e82eb19b154b0ac9563696035e283) | Update README.md | `mods/local-inventory/README.md` |

## 采纳方法

按主 [README](README.md) 执行。`contributor_text` 是作者原文，`suggested_text` 在此类条目中仅为供复核的候选，不代表无条件采纳。`review_status` 的协议警告优先于自动迁移；对实际生效源做逐键比对、冲突检查和分层验收。记录采用或未采用原因，并继续保留作者归属。
