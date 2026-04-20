# LLM-based-Software-Devlopment-Kit-Suite
share some tools for intelligence software development based LLM.

develop some tools for intelligence software development based LLM, such as context builder, personalized prompt and context management, task knowledge base builder.include:simple clean and crawler,clean and convert the document and file as .md

## 1,such as context builder
- Crawler 
- clean and convert the document and file as context text
## 2,[personalized prompt and context management](https://github.com/zhyr/HaxiTAG-Assistant)
## 3，task knowledge base builder
- Extract specific content as a dedicated task knowledge base
- clean and extractor tool
## 4，context rebuilder for different model API
- rewrite for knowledge enhancement and infomation strenthen
_ follow the Yueli KGM context structure by five semantic layers

## 5, git-tidy 如何使用？

#### 方式 A：直接运行
你可以指定任何目录进行清理：
```bash
~/git-tidy.sh ~/work      # 清理工作目录
~/git-tidy.sh .           # 清理当前目录
```

#### 方式 B：变成全局指令（推荐）
如果你希望在任何地方直接输入 `git-tidy` 就能用，可以执行：
```bash
sudo mv ~/git-tidy.sh /usr/local/bin/git-tidy
```
之后你只需要输入：
```bash
git-tidy
```

报错和冗余输出都重定向到了 `/tmp/git-tidy.log`，保持终端界面整洁。

这个工具现在非常适合处理你这种拥有大量微服务或多个鸿蒙/前端模块的开发环境。

## 6, code agent tools
[统计分析到处本地coding agent的prompt和历史记录](https://github.com/zhyr/Al-exporter)

## 7，bookmarklet
轻量级的将当前网页转换markdown文本并提供Gemini chatbot交互，
（1）拖拽bookmarklet到浏览器收藏夹的书签栏
（2）在访问的目标页面上点击这个书签栏的bookmarklet "Smart Reader Pro"

