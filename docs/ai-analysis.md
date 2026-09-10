# AI Analysis & Scoring Engine — AI Interview Coach

## Decoupled Scoring Architecture
Scores are computed across independent dimensions:
1. **Technical Knowledge (30%)**: Concept matching with `expected_concepts` & `ideal_answer`.
2. **Answer Quality (20%)**: Depth and explanation structure.
3. **Communication (15%)**: Speech pacing and filler word frequency.
4. **Project Understanding (10%)**: Ownership and architectural trade-offs.
5. **Presentation (10%)**: Eye Contact % and face posture stability.
6. **Filler Words (5%)**: Inverse penalty of filler frequency.
7. **Speaking Rate (5%)**: Balance relative to optimal 110–160 WPM window.
8. **Pause Management (5%)**: Silence density.

## Computer Vision Signal Ethics
MediaPipe Face Mesh and OpenCV measure:
- Eye Contact %
- Face Visibility
- Head Pose Yaw & Pitch
- Expression Classification (Neutral, Happy, Serious)

Expressions are presented strictly as approximate computer-vision signals without medical, psychological, honesty, or personality claims.
