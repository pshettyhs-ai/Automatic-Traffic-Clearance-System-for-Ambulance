# References

Carried over from the original project report's literature survey and bibliography, reformatted as
Markdown for easier linking from the rest of this repository.

## Literature reviewed during design

1. Rajurkar, S. P. "Traffic Management and Signal Manipulation System using Machine Learning." 2024.
   Reported 80.5% mAP50 vehicle detection (YOLOv8) on Indian traffic footage — the reference point cited
   in `ai_model/README.md` for what to expect before project-specific fine-tuning.
2. Satyakumar, M. "Emergency Vehicle Signal Pre-emption System for Heterogeneous Traffic Condition: A
   Case Study in Trivandrum City." 2019. Reported 25–30% emergency-vehicle delay reduction from signal
   pre-emption — informed the target response-time goals in this project's objectives.
3. Gupta, D. "Computer Vision Based Traffic Monitoring System." 2024.

## Cited in the original report's "Related Technologies" section

- Shi, W., Cao, J., Zhang, Q., Li, Y., & Xu, L. (2016). "Edge computing: Vision and challenges." *IEEE
  Internet of Things Journal*, 3(5), 637-646.
- Hassan et al. (2018) — edge vs. cloud latency for object detection (cited as 3-5s cloud vs. <500ms
  edge in the original report's literature survey).
- Kumar & Singh (2020) — bandwidth reduction from local vs. cloud video processing.
- David et al. (2019) — TensorFlow Lite on ARM Cortex-M microcontrollers.
- Janapa Reddi et al. (2020) — Edge Impulse optimization benchmarks.
- Han et al. (2016) — neural network compression via quantization/pruning/distillation.
- Stanford-Clark, A., & Truong, H. L. (2013). MQTT protocol design for unreliable networks.
- Pimentel, V., & Nickerson, B. G. (2012). WebSocket vs. HTTP polling bandwidth/latency comparison.

## Full original bibliography

- Bullock, D., Morales, J. M., & Sanderson, B. (2004). "Impact of signal preemption on the operation of
  the Virginia Route 7 corridor." *ITE Journal*, 74(3), 18-23.
- Fette, I., & Melnikov, A. (2011). "The WebSocket Protocol." RFC 6455, IETF.
- Howard, A. G., et al. (2017). "MobileNets: Efficient convolutional neural networks for mobile vision
  applications." *arXiv:1704.04861*.
- Hunt, P. B., Robertson, D. I., Bretherton, R. D., & Winton, R. I. (1981). "SCOOT — A traffic responsive
  method of coordinating signals." TRRL Report LR 1014.
- Janahan, S. K., Veeramanickam, M. R. M., Arun, S., & Narayanan, K. (2018). "IoT based smart traffic
  signal monitoring system using vehicles count." *IJET*, 7(2.21), 309-312.
- Miller, A. J. (1963). "Settings for fixed-cycle traffic signals." *Operations Research*, 11(6), 895-912.
- Redmon, J., Divvala, S., Girshick, R., & Farhadi, A. (2016). "You only look once: Unified, real-time
  object detection." *Proceedings of IEEE CVPR*, 779-788.
- Rizwan, P., Suresh, K., & Babu, M. R. (2016). "Real-time smart traffic management system for smart
  cities by using Internet of Things and big data." ICETT.
- Robertson, D. I. (1969). "TRANSYT: A traffic network study tool." Road Research Laboratory Report LR 253.
- Roy, S., & Rahman, M. S. (2019). "Emergency vehicle detection on heavy traffic road from CCTV footage
  using deep convolutional neural network." ICECCE.
- Tan, M., & Le, Q. (2019). "EfficientNet: Rethinking model scaling for convolutional neural networks."
  *ICML*, 6105-6114.
- Viola, P., & Jones, M. (2001). "Rapid object detection using a boosted cascade of simple features."
  *Proceedings of IEEE CVPR*, 1, 511-518.
- Wang, Z., Liu, H., & Zhang, T. (2020). "Emergency vehicle detection using temporal information in
  video sequences." *IEEE Transactions on Intelligent Transportation Systems*, 21(4), 1456-1468.

## Technology choices made in this revision, and why (not in the original report)

These weren't in the original literature survey, since they reflect this revision's architecture
changes — listed here for completeness:

- [Ultralytics YOLOv8 documentation](https://docs.ultralytics.com/) — model selection and training API.
- [MQTT.org / OASIS MQTT v3.1.1 spec](https://mqtt.org/) — broker/protocol choice for emergency events.
- [Socket.IO documentation](https://socket.io/docs/) — WebSocket bridge for the dashboard.
- [better-sqlite3](https://github.com/WiseLibs/better-sqlite3) — synchronous SQLite driver, chosen for
  simplicity in a single-process Node backend over async alternatives.
