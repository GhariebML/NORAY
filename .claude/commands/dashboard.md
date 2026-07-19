# /dashboard

Show a unified dashboard of all tracked applications (jobs + scholarships)
with analytics, pipeline status, and actionable insights.

## Instructions

1. Load the career profile from `career_profile.json`
2. Run the dashboard analytics:
   ```python
   from NORAY.dashboard.analytics import get_analytics_summary, format_analytics
   from NORAY.dashboard.applications import get_all_applications, get_pipeline_stats, get_upcoming_actions
   from NORAY.shared.profile_store import load_profile

   profile = load_profile()
   analytics = get_analytics_summary()
   apps = get_all_applications()
   pipeline = get_pipeline_stats()
   actions = get_upcoming_actions(days=14)
   ```
3. Display the formatted analytics using `format_analytics(analytics)`
4. Show pipeline visualization:
   - Jobs: discovered → applied → interview → offer
   - Scholarships: discovered → preparing → submitted → interview → awarded
5. Show upcoming actions (deadlines, interviews, follow-ups in next 14 days)
6. Display top 3 insights from `analytics["insights"]`

## Output Format

```markdown
# 📊 NORAY Dashboard

## Pipeline Overview
| Stage | Jobs | Scholarships |
|-------|------|-------------|
| Discovered | X | X |
| Applied/Submitted | X | X |
| Interview | X | X |
| Offer/Awarded | X | X |

## 📈 Key Metrics
- Response Rate: XX%
- Interview Rate: XX%
- Offer Rate: XX%
- Scholarship Success: XX%

## 🔜 Upcoming Actions (14 days)
- [Type] Name — Action (Date, X days)

## 💡 Insights
- Insight 1
- Insight 2
- Insight 3

## 📅 Monthly Activity
- 2026-05: ████████ (8)
- 2026-04: ██████ (6)
```

Present a clean, scannable dashboard that helps the user understand their application pipeline at a glance.
