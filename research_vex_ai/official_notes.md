# Official VEX AI Notes

Date checked: 2026-03-30

## Current-season facts
- RECF's VAIRC resource page says the current game is **Push Back** for the **2025-2026** season.
- The VAIRC page states matches use a **15 second Isolation Period** followed by a **1:45 Interaction Period**.
- The same page says the field has **88 Blocks**, **4 Goals** and **2 Park Zones**.
- The VAIRC resource page links the **game manual**, **Q&A**, and notes that teams should monitor the VEX Forum and official Q&A for clarifications during the season.

## Software-relevant facts
- VEX's V5 AI competition page describes VEX AI as a **two-robot** team system with **no drivers** during match play.
- The VEX GPS documentation exposes field-relative position and heading APIs, including `xPosition`, `yPosition`, `heading`, and `setLocation`.
- The VEXlink documentation exposes robot-to-robot communication through `message_link` and `serial_link`.
- VEX's "Coding the VEX AI Robot" article says VAIRC code should explicitly account for the two autonomous segments, Isolation first and Interaction second.
- That same article notes the Jetson / AI data update rate is about **15 Hz**, which is a useful upper bound for perception polling.

## R&D implications
- Start with a planner that is aware of **phase changes**: Isolation and Interaction should not share identical behavior.
- Build software around a **shared world state** model so GPS, AI detections, and partner-link messages feed one decision layer.
- Treat robot-to-robot communication as a first-class subsystem from day one, not an afterthought.
- Keep early logic portable and testable on a laptop before porting it to a VEXcode project.

## Official sources
- https://vairc-kb.recf.org/hc/en-us/articles/18046519545879-Game-Manual-and-Resources-for-VEX-AI-Robotics-Competition-Teams
- https://www.vexrobotics.com/v5/competition/vex-ai
- https://api.vex.com/v5/home/cpp/Sensing/GPS.html
- https://api.vex.com/v5/home/cpp/VEXlink/MessageLink.html
- https://kb.vex.com/hc/en-us/articles/360049619171-Coding-the-VEX-AI-Robot
