



# AIWEEKADVANCEDVISION

**AI Assistant with Secure Face Verification**  
An end-to-end, voice-enabled personal assistant gated by fast, accurate facial verification. Built for real-world use where security, latency, and explainability matter.

---

## 📹 Demo Video

<video width="500" controls>
  <source src="/test_samplemp4.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

> Located at https://www.youtube.com/@omarawad117 

---

## Report

> Located at `/Hackathon Report` in the repository.

---

## 🌐 Live Demo

You can try the full hosted assistant experience at:  
👉 **[https://tuvcontrol.horizonaii.com/](https://tuvcontrol.horizonaii.com/)**

---

#Executive Summary

This project delivers a Personal AI Assistant protected by a CNN-based face verification login. Users authenticate by presenting a face image (live capture or upload). The system matches the image to user-specific templates created at enrollment; access is granted/denied accordingly, with all failed attempts logged and escalated.

Upon authentication, users access a server-hosted assistant that aggregates cross-domain signals—health, finance, and calendar—to produce real-time, voice-enabled analytics and recommendations. Centralized inference reduces client-side compute, improves scalability, and enables multi-source insights, such as:

Elevated stress scores aligned with densely packed meeting blocks.

Higher daily heart-rate averages on days with large discretionary spending and outdoor activities.

---

## Features

Secure Face Login (1:1 verification) — K-template matching with calibrated thresholds (target FAR ≤ 0.1%).

Voice Assistant — Full-duplex, near real-time conversation with barge-in.

Cross-Domain Reasoning — Merges finance, health, and calendar streams for causal hints and correlations.

On-Device/Server Flexibility — CPU baseline; GPU-boosted path for low-latency embeddings.

Audit & Escalation — Every failed attempt logged with username, IP, timestamp, and similarity score.

Admin Portal — Enrollment, user management, log monitoring, exports.

Privacy & Access Control — Role-aware data views and least-privilege service tokens.

Clean UI — Dark/light themes, responsive layout, accessible keyboard navigation.

---

## Architecture

High-level components:

Face Verification Service

Face detection: HOG (CPU) or CNN (GPU).

Embedding: 128-D, L2-normalized vectors.

K-means template store per user (3–8 centroids typical).

Online scorer: cosine similarity against templates, thresholded by τ.

Assistant Core

Centralized inference service (LLM-backed) with retrieval over user data.

Data connectors: health (wearables), finance (bank/expense exports), calendar (Google/Microsoft).

Event correlator and rules engine for lightweight, explainable insights.

APIs

/auth/verify: login via image → access token on success.

/admin/*: enrollment, template refresh, log export.

/assistant/*: voice session, analytics queries, scheduled reports.

Data Plane

Enrollment images (private storage).

Templates (.npy per user).

Auth logs (structured JSON + CSV export).

Optional vector index snapshot for drift analysis.

Frontend

Login with live capture or upload.

Voice UI with interruption.

Dashboards for trends, correlations, and admin views.

---

## Face Verification at Low Latency
Task Definition

Problem: 1:1 verification — does the query image belong to the claimed identity?

Constraints:

Images per user: 100–1500 (duplicates + low quality included).

Latency: ≤500 ms end-to-end on CPU; <50 ms target on GPU.

Security: FAR ≤ 0.1% (False Accept Rate).

Baseline (for comparison)

Extract 128-D embeddings (e.g., dlib/face_recognition).

Compare query to all stored embeddings for the user; accept if distance < threshold.

Pain points: High latency (hundreds of comparisons), noisy thresholds, redundancy from duplicates.

Final Pipeline (Optimized)

Preprocessing

Face detect with HOG (CPU) or CNN (GPU).

Quality gates:

Laplacian variance ≥ 40 (blur filter).

Min face box ≥ 64 px.

Deduplicate embeddings (cosine ≥ 0.995 → duplicates).

Embedding

Produce 128-D, L2-normalized vectors.

Dominant cost on CPU: ~350–400 ms.

Template Generation (Enrollment, Offline)

K-means per user.

K = min(5, floor(N/12)) → typically 3–8 templates.

Persist as small .npy files.

Verification (Online)

Embed query → vector q.

Load templates T ∈ ℝ^{K×128}.

Score: s = maxᵢ ⟨q, Tᵢ⟩ (cosine).

Accept if s ≥ τ (calibrated).

Threshold Calibration

Held-out splits (70/30).

Track TPR, FPR, EER, Best-F1.

Pick τ at FAR ≈ 0.1%.

Why K-Templates Help

Single mean centroid collapses pose/lighting modes.

Multiple centroids preserve frontal/profile, glasses/no-glasses, lighting variations.

Online max-cosine selects the best mode → robust genuine scores with suppressed impostors.

Reduces comparisons from 100–150 embeddings to 3–8 templates → faster and stabler.

Performance Results

Two-user sanity test

EER = 0.0, Best-F1 = 1.0.

TPR = 100%, FPR = 0%.

Scoring latency: 0.06 ms; embedding: ~353 ms (CPU).

50-user stress test

τ ≈ 0.898 → TPR = 100%, FPR ≈ 0.098%
(~4 false accepts out of 4,067 impostor trials).

Embedding latency: p50 = 390 ms, p95 = 439 ms (CPU).

Scoring latency: p50 = 0.01 ms.

Admin Portal (Built from Scratch)

User Management

Bulk enroll via folder uploads.

Optional overwrite of existing templates.

Scales to 50+ identities.

Log Monitoring

Dashboard for successes, failures, daily totals.

Metadata captured: username, IP, timestamp, similarity score.

Visual indicators; CSV export for audits.

Assistant Intelligence

Voice interaction with interruption (barge-in).

Analytics layer blends signals:

Stress vs. meeting density.

Heart-rate vs. spend and outdoor time.

Sleep vs. next-day productivity proxies.

Actions & Automations

Natural-language tasks: “Send weekly wellness report,” “Brief me before 9am.”

Scheduler triggers analytics → emails/dashboards to authorized recipients.

---

## 🧪 API Test Script

You can test the assistant backend directly using:

```bash
python test_model_api.py
