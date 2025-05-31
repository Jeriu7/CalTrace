
---

## 🧭 使用步骤简述

1. **运行 `ConvertVideo-1.1.2.py`**  
   - 转换 `.mov/.mp4` 为 `.avi`  
   - 重命名 `.czi` 文件，补充 `fps` 信息

2. **运行 `CalTrace_Script-1.1.2.py`**  (将其拖入ImageJ插件文件夹中后重启ImageJ，可以直接运行)
   - 创建项目结构  
   - 自动启动 ROI 交互式标注（基于 IJ Macro）  
   - 自动执行时间序列分析  
   - 输出并格式化 CSV 文件  
   - 引导手动分组分类  
   - 执行数据整合 + 归一化处理

---

## 🔧 运行环境要求

- **ImageJ / Fiji**（支持 Jython 环境）
  - ImageJ 1.54g, Java 1.8.0_322(64-bit)
- **插件依赖：**
  - `Time_Series_Analyzer_V3`
- **外部工具：**
  - `ffmpeg`（用于视频格式转换，需配置到系统环境变量）

---

## 📖 延伸阅读与教程

- 📝 v1.0 教程：[CSDN 博客 - 原始工作流说明](https://blog.csdn.net/Jeriu/article/details/144804954)
- 🆕 v1.1.2 更新说明博客：*Coming Soon*

---

## 📬 联系作者

如你在使用中遇到问题或有建议，欢迎提交 Issue 或私信联系我：

- Email: `zekun.wu@qq.com`  
- CSDN: [Jeriu](https://blog.csdn.net/Jeriu)

---

## 📄 License

MIT License - 仅用于科研与教学用途，若用于商业分析请联系作者授权。
