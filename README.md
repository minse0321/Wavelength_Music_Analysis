# 🎵 Wavelength Music App — User Behavior Analysis

## Overview
Simulated event data analysis for a music streaming app ("Wavelength").  
800 virtual users × 60 days of behavioral events were generated and analyzed  
to understand retention, funnel conversion, and subscription drivers.

## Key Insight
> **Early engagement predicts conversion: more plays, fewer skips.**  
> Users who play more songs and skip less in the first 3 days  
> are significantly more likely to convert to premium subscription.

## Tech Stack
- **Python** (numpy, pandas, matplotlib) — data simulation & EDA
- **Tableau Public** — interactive dashboard
- **Google Colab** — analysis environment

## Project Structure

├── generate_events.py        # Simulates 800 users × 60 days of events

├── wavelength_eda_analysis.ipynb  # EDA notebook (retention, funnel, segmentation)

├── events_raw.csv            # Generated event log (241,956 rows)

└── users_meta.csv            # User metadata with persona labels

## User Personas (5 types)
| Persona | Description | Subscribe Rate |
|---|---|---|
| Heavy | Daily active, low skip rate | 67% |
| Convert | Moderate usage, converts mid-journey | 55% |
| Light | 2-3x/week, steady | 22% |
| Churn | Active early, fades out | 12% |
| New Dropoff | Leaves within 1-3 days | 1.5% |

## Analysis Summary
1. **Retention Curve** — Day 0~3 shows steepest drop (100% → 70%)
2. **Funnel Analysis** — Biggest drop-off at play_song → subscribe_premium (28% conversion)
3. **Persona Heatmap** — Heavy/Convert users drive subscription; Churn/Dropoff barely convert
4. **Plays vs Subscribe** — Subscribers play 3x more songs than non-subscribers

## Dashboard
🔗 [View on Tableau Public](https://public.tableau.com/views/Wavelength_User_Behavior_Analysis/WavelengthUserBehaviorDashboard)
