# Image Post Summary Instructions

Use these instructions to generate a structured summary from a Xiaohongshu image post.
The images have already been downloaded. Read each image to extract its text content,
then combine with the post metadata to produce summary.md.

---

## Step 1 — Read the post metadata

Read `post.txt` in the post directory. It contains the title (first line) and
the author's caption/description.

Read `.meta.json` for structured metadata (title, URL, uploader, image count).

## Step 2 — Read all images

Read every image file in the directory (`01.jpg`, `02.jpg`, …) using the Read tool.
For each image, extract:
- All visible text (slide text, overlays, captions printed on the image)
- The main topic or message of that slide

Compile a full ordered list of the extracted text across all slides.

## Step 3 — Generate summary.md

Write `summary.md` to the post directory using the output format below.
Write in the **same language** as the post content (Chinese post → Chinese summary).

---

## Output Format

```markdown
# {{TITLE}}

## 基本信息

| 字段 | 内容 |
|------|------|
| 平台 | 小红书 (Xiaohongshu) |
| URL | {{URL}} |
| 作者 | {{UPLOADER}} |
| 图片数量 | {{IMAGE_COUNT}} 张 |

## 内容概述

> 2-3句话概括这篇图文帖的核心主题和价值。

## 核心要点

- 要点 1
- 要点 2
- 要点 3
- …

## 逐图内容

### 第1张
提取的文字内容 + 简要说明这张图讲了什么

### 第2张
提取的文字内容 + 简要说明这张图讲了什么

（按实际图片数量继续）

## 作者原文摘录

> 从 post.txt 的描述中摘录最有价值的段落或金句

## 相关话题

- 话题标签1
- 话题标签2
- …
```

---

## Instructions

1. Write in the **same language** as the post (Chinese post → Chinese summary).
2. Extract text from images faithfully — do not paraphrase or omit slide text.
3. If an image is decorative (no meaningful text), note it briefly and move on.
4. Keep "内容概述" concise; make "逐图内容" thorough and complete.
5. Hashtags from post.txt go in "相关话题" (strip `#` and `[话题]` formatting).
6. Save the result as `summary.md` in the same directory as the images.
