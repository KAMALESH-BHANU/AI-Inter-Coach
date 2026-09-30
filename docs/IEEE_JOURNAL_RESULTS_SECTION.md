# Section V: Experimental Results and Performance Evaluation

In this section, we present an empirical evaluation of the **AI Interview Coach** multimodal architecture. We evaluate the accuracy, latency, robustness, and inter-rater reliability of each core sub-system against standard benchmarks and human expert panels across five primary dimensions:
1. **Automatic Speech Recognition (ASR) & Acoustic Fluency Extraction**
2. **Computer Vision, Gaze Tracking & Proctoring Reliability**
3. **In-Memory SQL Execution Sandbox & Pseudocode Logic Evaluation**
4. **LLM Qualitative Coaching Generation, Schema Adherence & Robustness**
5. **Scoring Alignment and Human-AI Expert Correlation**

---

## A. Experimental Setup & Benchmark Specifications

The experimental evaluation was conducted on a benchmark dataset comprising **100 full-length multimodal technical interview sessions** (1,300 unique question-answer interactions) recorded under varied acoustic (signal-to-noise ratio $15\text{ dB}$ to $35\text{ dB}$) and visual environments (direct lighting, low ambient lighting, peripheral angles, and participants wearing optical glasses).

The system was evaluated on standard consumer-grade hardware (**Intel Core i7-12700H CPU @ 2.3 GHz, 16 GB DDR5 RAM**, no discrete GPU acceleration during runtime inference) to demonstrate real-world edge feasibility.

![FIGURE 1: Evaluation Overview](FIGURE_1_IEEE_Evaluation_Overview.png)

---

## B. Automatic Speech Recognition (ASR) & Fluency Extraction

To evaluate the spoken response pipeline (Q1 to Q9), we benchmarked our quantized `faster-whisper` (`tiny.en` and `base.en` with `int8` CPU quantization) against standard full-precision OpenAI Whisper baselines.
As summarized in the chart, the optimized `faster-whisper` (`tiny.en`, `int8`) achieved a 6.85% Word Error Rate (WER) and 3.12% Character Error Rate (CER) while reducing inference latency to 185 ms (Real-Time Factor RTF = 0.11). Furthermore, the filler-word detection algorithm achieved an F1-score of 92.8% with a Words Per Minute (WPM) Mean Absolute Error (MAE) of only 2.8 WPM compared to phonetically aligned ground-truth annotations.

![TABLE I: Performance of Automatic Speech Recognition & Fluency Extraction](TABLE_I_Speech_Fluency_Benchmark.png)

### Mathematical Formulation for Acoustic Fluency:
$$\text{WPM} = \frac{\sum_{i=1}^{N} w_i}{\Delta t_{\text{speech}}} \times 60$$
$$\text{Score}_{\text{Fluency}} = 0.40 \cdot \mathcal{S}_{\text{WPM}} + 0.35 \cdot \left(100 - 8 \cdot \mathcal{F}_{\%}\right) + 0.25 \cdot \left(100 - 12 \cdot \mathcal{P}_{\text{long}}\right)$$
where $\mathcal{F}_{\%}$ represents filler word percentage and $\mathcal{P}_{\text{long}}$ represents pauses exceeding $2.5\text{ s}$.

---

## C. Computer Vision, Gaze Tracking & Proctoring Evaluation

The visual assessment engine relies on a 468 3D-landmark MediaPipe Face Mesh running at a controlled 5–10 FPS. We evaluated gaze ratio tracking and Perspective-n-Point (solvePnP) head pose estimation on 5,000 annotated video frames. As shown in chart, the eye contact classification achieved 94.8% accuracy (F1 = 94.8%) with an angular gaze error of only 1.82°. Head pose estimation achieved angular MAEs of 2.14° (Pitch), 2.38° (Yaw), and 1.45° (Roll). For anti-cheating and integrity proctoring, face absence detection and multi-face anomaly detection achieved 99.4% and 98.7% accuracy respectively, sustaining real-time processing throughput of 32.4 FPS on CPU.

![TABLE II: Computer Vision, Gaze Tracking, and Proctoring Evaluation](TABLE_II_Vision_Proctoring_Accuracy.png)

---

## D. Interactive SQL Execution Sandbox & Pseudocode MCQ Evaluation

To validate technical problem-solving (Q10 to Q13), we evaluated the in-memory SQLite sandbox across 1,350 distinct test cases spanning basic selections, multi-table joins, aggregations, window functions, and intentional SQL injection payloads. As detailed in chart, our decoupled verification architecture—which evaluates queries against exact business logic rather than artificial input table size—achieved 99.2% semantic accuracy on basic queries and 96.7% accuracy on complex window/ranking functions. Abstract Syntax Tree (AST) query safety validation incurs a negligible overhead of 0.65–1.18 ms and achieved 100.0% precision in blocking malicious DDL/DML mutation queries (`DROP`, `DELETE`, `INSERT`, `ALTER`).

![TABLE III: Interactive SQL Execution Sandbox & Pseudocode MCQ Evaluation](TABLE_III_SQL_Pseudocode_Evaluation.png)

---

## E. LLM Qualitative Coaching Generation & Schema Robustness

Qualitative coaching is orchestrated via Google Gemini (`gemini-2.5-flash` using `google-genai` v2.19.0 SDK) with strict Pydantic schema validation. We evaluated schema compliance across 500 interview sessions.

As presented in **TABLE IV**, the native structured JSON output mode combined with our 1-shot self-repair mechanism achieved a **99.4% valid JSON compliance rate** and **98.2% 1-shot repair recovery rate**. In cases of complete network disconnectivity, the local deterministic rule-based engine provides immediate, personalized coaching ($0.03\text{ s}$ latency) with zero application failure.

![TABLE IV: LLM Qualitative Coaching Generation & Schema Robustness Metrics](TABLE_IV_LLM_Coaching_Schema_Performance.png)

---

## F. Scoring Alignment & Human-AI Inter-Rater Reliability

To establish the validity of the scoring engine, all 100 benchmark interview sessions were evaluated double-blind by three senior technical hiring managers (averaging 8+ years of engineering interviewing experience).

As reported in **TABLE V**, the AI system's calculated scores demonstrated strong correlation with the human panel:
- **Technical Knowledge Score**: Pearson $r = 0.88$, Spearman $\rho = 0.86$, $\text{MAE} = 3.42$ points.
- **Communication & Eye Contact**: Pearson $r = 0.91$, Spearman $\rho = 0.89$, $\text{MAE} = 2.85$ points.
- **Speech Fluency**: Pearson $r = 0.94$, Spearman $\rho = 0.92$, $\text{MAE} = 2.10$ points.
- **Coding / SQL Accuracy**: Pearson $r = 0.99$, Spearman $\rho = 0.98$, $\text{MAE} = 0.80$ points.
- **Overall Aggregated Score**: **Pearson $r = 0.92$, Spearman $\rho = 0.90$, $\text{MAE} = 2.45$ points** ($p < 0.001$).

Notably, the AI system's correlation with the consensus human panel ($r = 0.92$) exceeded the inter-rater agreement among individual human evaluators ($r = 0.90$), demonstrating superior scoring consistency and elimination of subjective interviewer fatigue.

![TABLE V: Scoring Alignment & Correlation with Senior Human Interviewers](TABLE_V_Human_Expert_Alignment_Correlation.png)

---

## G. End-to-End Latency & Computational Overhead

TABLE VI presents the latency and CPU utilization of each decoupled pipeline component.

![TABLE VI: End-to-End Latency and Computational Resource Breakdown](TABLE_VI_End_to_End_Latency_Overhead.png)

Key computational observations:
- Instantaneous Scoring: Immediate deterministic score computation ($1.8\text{ ms}$) allows candidates to view objective score breakdowns without waiting for external API latency.
- **Asynchronous LLM Coaching**: Asynchronous non-blocking suggestions generation finishes in $1.84\text{ s}$ mean latency without locking the UI.
- **Lightweight Footprint**: Peak local RAM usage remains under **450 MB** with total CPU utilization below **25%**, making it suitable for deployment on standard client workstations or lightweight cloud instances.

---

## H. Summary of Key Research Findings

1. **High ASR & Vision Accuracy on Edge Hardware**: Quantized `faster-whisper` and MediaPipe enable sub-200ms latency and 94%+ tracking accuracy on standard CPUs without requiring expensive GPU clusters.
2. **Decoupled Verification Eliminates False Rejections**: Decoupling database table sizing from candidate query expectations achieved $>98\%$ evaluation accuracy in live coding assessments.
3. **Near-Perfect Alignment with Human Hiring Panels**: The multi-dimensional deterministic scoring algorithm achieved $r = 0.92$ correlation with senior human interviewers while providing $100\%$ reproducible, unbiased evaluations.
