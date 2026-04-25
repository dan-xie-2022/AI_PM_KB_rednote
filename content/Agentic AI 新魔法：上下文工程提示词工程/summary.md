# Agentic AI 新魔法：上下文工程>提示词工程

## 基本信息

| 字段 | 内容 |
|------|------|
| 平台 | 小红书 (Xiaohongshu) |
| URL | https://www.xiaohongshu.com/explore/689abc860000000025019c06?xsec_token=ABZbdYZJD8ekqCLZrMSpk-p5MBhCLmfY1sLH-Ztb0szLE=&xsec_source=pc_collect |
| 作者 | HaileyZhy |
| 图片数量 | 7 张 |

## 内容概述

> 本文系统介绍 Context Engineering（上下文工程，CE）的5W1H——从定义、与Prompt Engineering的区别、作用、使用方法到应用前景。核心观点：大多数Agent错误不是模型错误而是上下文错误，CE通过系统化管理模型输入的所有内容来提升Agent能力，正在替代传统PE成为Agentic AI必备技术。

## 核心要点

- Context = 模型生成输出前接收的**所有内容**（不只是用户消息），包含7个组成部分
- CE与PE的核心区别：PE关注"如何响应"，CE关注"收集LLM完全实现目标所需的全部信息"
- 大多数Agent错误是上下文错误，不是模型错误——CE直接解决这个根本问题
- CE当前价值：减少AI错误、确保一致性、实现复杂多步骤任务、支持自我纠正循环
- CE是对当前Multi-agent system问题的最佳工程补丁，但当模型更强时其价值会递减
- 长期来看，AGI的额外价值空间将转向交互体验、认知外包和数据再生产，CE退居"个性微调"角色

## 逐图内容

### 第1张
**封面 + Context 构成图**
标题：Context Engineering 上下文工程的5W1H（全文1692字，阅读需5分钟，作者 HaileyZhy）
核心定义：CE通过系统化上下文管理提升AI Agent处理复杂任务的能力，替代传统Prompt Engineering。
图示展示Context的7个组成部分（韦恩图）：Instructions/System Prompt、User Prompt、State/History (short-term Memory)、Retrieved Information (RAG)、Long-term Memory、Available Tools、Structured Output。

### 第2张
**本文缘起**
目录：什么是CE / CE和PE的区别 / CE有什么作用 / 如何使用CE / CE最佳实践 / CE应用前景
背景：2024年6月25日Karpathy转发Shopify CEO推文强调Context engineering重要性；7月19日Manus Peak发布构建Agent Context Engineering的经验分享文章，CE开始替代PE，成为处理复杂任务的Agent必备技术。

### 第3张
**什么是CE**
Context（上下文）= 模型生成输出前接收的所有内容，7个组成部分详解：
- **Instructions / System Prompt**：定义模型在对话期间行为的初始指令集，含examples和rules
- **User Prompt**：用户输入的即时任务或问题
- **State / History (short-term Memory)**：当前对话，此刻之前的用户和模型响应
- **Long-term Memory**：长期知识库，含用户偏好、历史项目摘要等
- **Retrieved Information (RAG)**：外部最新知识，来自文档、数据库或API
- **Available Tools**：可调用的所有函数或内置工具的定义
- **Structured Output**：模型响应格式定义，如JSON对象

### 第4张
**CE有什么作用**
对比PE：之前Agent优化focus在输出方式（如ReAct框架）；CE强调在调用LLM之前，先收集LLM完全实现目标所需的信息。
比喻：Agent是厨师，炒菜的火候和调料顺序重要，但食谱和原料准备同样重要。
CE的作用：
- 减少AI错误：大多数Agent错误是上下文错误，不是模型错误
- 确保一致性：AI能循环遵循项目模式和规则惯例
- 实现复杂功能：AI在合适上下文中可处理多步骤任务
- 自我纠正：验证循环允许AI修复自己的错误

### 第5张
**如何使用CE**
构建完整CE需要check的方面：
- 设计和管理 prompt chains
- 调整指令或系统提示词
- 管理提示词的动态变量（用户输入、日期、时间等）
- 搜索和准备相关知识（RAG）
- 增强查询 query augmentation
- 在构建Agent系统时进行工具定义与说明
- 准备和优化 few-shot demonstrations
- 构建输入和输出格式（分隔符 JSON模式）
- 短期记忆（状态/历史上下文）和长期记忆（向量存储中检索相关知识）

### 第6张
**最后想说（CE的定位与局限）**
CE是对Multi-agent system应用现有问题打补丁的最佳工程实践。
比喻：CE是让菜更加色香味俱全的调料——把现有能吃但填不饱肚子的菜做得更好。
**局限性**：当模型更强时CE价值递减——当模型对上下文、工具、环境的理解趋近人类水平，CE退到"安全护栏"与"个性微调"的位置，不再是"满汉全席全靠调料"。
AGI额外价值空间溢出方向：
- 交互体验：多模态、具身化、情感化（陪聊、陪学、陪玩）
- 认知外包：把人类不想做的"思考模块"直接托管（择校、择业、择偶等决策）
- 数据再生产：让AGI把行业暗数据、长尾知识"蒸馏"成可复用的"认知资产"

### 第7张
**结尾**
当模型逼近AGI时，"Agent-复杂任务执行器"的叙事会被淡化，AGI核心价值将转向「与人类共创意义」——让交互更自然，让决策更轻盈，让数据更增值；CE则退居「让AI更懂你我」的轻量旋钮，不再是撑起商业壁垒的那堵墙。

## 作者原文摘录

> CE技术让大众看到解决Agent落地问题的曙光，通过回答以下6个问题搞清楚CE是啥！

> 大多数Agent错误不是模型错误，而是上下文错误。

> 如果把Agent应用比做一盘菜，那CE是让菜更加色香味俱全的调料，把现有的能吃但填不饱肚子也卖不起高价的菜做得更好吃更下饭更具备壁垒和商业价值。

> 当模型逼近AGI时，"Agent-复杂任务执行器"的叙事会被淡化，AGI的核心价值将转向「与人类共创意义」。

## 相关话题

- ai
- 上下文工程
- agent
- 提示词
- 硅谷
- vibecoding
