# 📜 TailLog Python (Kivy)

A lightweight, real-time Python GUI application built with the [Kivy](https://kivy.org/) framework for tailing and monitoring streaming application logs.

---

## 🎯 Purpose

This tool was internally developed to help monitor and understand application logs effectively. It allows developers to quickly investigate issues by tracking log outputs in real-time without the need for expensive, proprietary software.

> **Note:** This is a simple, lightweight log tailing tool designed for basic log monitoring. It is not intended to be a complete feature-for-feature replacement for commercial tools like Baretail Pro or Baregrep Pro.

## ✨ Features

- **Real-Time Tailing:** Seamlessly follow streaming log files (similar to `tail -f` behavior).
- **Search & Highlight:** Search for specific phrases, navigate through matches, and highlight critical log entries.
- **Smart Scrolling:** Automatically scrolls to the newest log entries or allows manual navigation.
- **Cross-Platform GUI:** Built on Kivy, providing a consistent UI experience.

## 🚀 Usage

To launch the log tailing GUI, simply run the following command in your terminal:

```bash
python logtail_gui.py
```

## 🛠️ Context

This application was created to provide a deeper understanding of App logs. By providing a clear GUI with accessible navigation buttons and widgets, it makes it significantly easier to trace application behavior, investigate bugs, and provide timely fixes.
