# R73 RC1 Source Preview

PvZH AM is an unofficial community Mod project for the international edition of *Plants vs. Zombies Heroes*. Electronic Arts Inc. owns the original game's code, materials and related trademarks. EA and PopCap have given no endorsement and bear no responsibility for the project's content or operation. [EA Plants vs. Zombies Mod Policy](https://help.ea.com/en/articles/plants-vs-zombies/mod-policy/)

PvZH AM 是面向国际版《植物大战僵尸：英雄》的非官方社区 Mod 项目。原游戏代码、素材及相关商标归 Electronic Arts Inc. 所有。EA 与 PopCap 未为本项目背书，也不对其内容或运行负责。 [EA《植物大战僵尸》Mod 政策](https://help.ea.com/en/articles/plants-vs-zombies/mod-policy/)

## Included source

These seven files match the source compiled into the R73 RC1 development build. The preview covers offline artwork processing and editor utilities. The Java files can be compiled with the JDK alone.

| File | Purpose |
| --- | --- |
| [`NativeArtworkPng.java`](src/com/pvzh/sharecode/NativeArtworkPng.java) | PNG and RGBA encoding and decoding |
| [`NativeTintColor.java`](src/com/pvzh/sharecode/NativeTintColor.java) | RGBA recoloring that preserves alpha |
| [`NativeTintParameters.java`](src/com/pvzh/sharecode/NativeTintParameters.java) | Color input validation and preview state |
| [`NativeArtworkParameters.java`](src/com/pvzh/sharecode/NativeArtworkParameters.java) | Artwork scale and placement parameters |
| [`NativeArtworkDocumentRequests.java`](src/com/pvzh/sharecode/NativeArtworkDocumentRequests.java) | Local PNG import and export request tracking |
| [`NativeManualTaxonomyLabel.java`](src/com/pvzh/sharecode/NativeManualTaxonomyLabel.java) | Display labels for editor selections |
| [`NativeMarkdown.java`](src/com/pvzh/sharecode/NativeMarkdown.java) | Markdown text and formatting parser |

## Source terms

The Java files in this preview are available for public review. The team has yet to choose general terms for reuse, modification or redistribution of AM source code. Rights remain with the respective holders, subject to applicable law and the platform terms. [Repository license scopes](../../../LICENSES.md)
