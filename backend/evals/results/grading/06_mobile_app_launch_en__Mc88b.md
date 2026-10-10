# Plan Mc88b — sample 06_mobile_app_launch_en

- Pipeline status: `ok`

## Tasks (49 tasks, 185 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 3 | — | Define v2 features and scope | A document with defined features and scope for v2. |
| O1-KR1.t2 | O1-KR1 | 4 | O1-KR1.t1 | Design UI for streaks and smart reminders | A set of UI mockups for streaks and smart reminders. |
| O1-KR1.t3 | O1-KR1 | 6 | O1-KR1.t2 | Implement streak tracking logic | Streak tracking logic implemented and tested. |
| O1-KR1.t4 | O1-KR1 | 6 | O1-KR1.t3 | Implement smart reminder logic | Smart reminder logic implemented and tested. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t4 | Test v2 features with internal users | Feedback from internal users on v2 features. |
| O1-KR1.t6 | O1-KR1 | 4 | O1-KR1.t5 | Revise v2 based on feedback | Revised version of v2 with changes from feedback. |
| O1-KR1.t7 | O1-KR1 | 3 | O1-KR1.t6 | Prepare for App Store and Google Play submission | All required assets and metadata uploaded for App Store and Google Play submission. |
| O1-KR1.t8 | O1-KR1 | 2 | O1-KR1.t7 | Submit v2 to App Store and Google Play | v2 submitted to App Store and Google Play with confirmation from both platforms. |
| O1-KR1.t9 | O1-KR1 | 3 | O1-KR1.t8 | Monitor app store reviews and ratings | At least 50 reviews collected and analyzed for the quarter. |
| O1-KR2.t1 | O1-KR2 | 3 | — | Define crash metrics and baseline | Baseline crash-free sessions recorded in Firebase Analytics with a note of 97.0%. |
| O1-KR2.t2 | O1-KR2 | 4 | O1-KR2.t1 | Identify crash causes | List of top 5 crash causes with associated crash logs and user reports. |
| O1-KR2.t3 | O1-KR2 | 6 | O1-KR2.t2 | Fix critical crash issues | Code changes pushed to the development branch with fixes for top 3 crash causes. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Test fixes in development | Test results showing no crashes in the fixed areas of the app. |
| O1-KR2.t5 | O1-KR2 | 3 | O1-KR2.t4 | Monitor crash-free sessions | Crash-free session data recorded in Firebase Analytics for the next 2 weeks. |
| O1-KR2.t6 | O1-KR2 | 4 | O1-KR2.t5 | Analyze crash-free session data | Analysis report showing current crash-free session percentage and progress toward the target. |
| O1-KR2.t7 | O1-KR2 | 5 | O1-KR2.t6 | Implement additional crash prevention | Code changes pushed to the development branch with additional crash prevention measures. |
| O1-KR2.t8 | O1-KR2 | 4 | O1-KR2.t7 | Test additional crash prevention | Test results showing no crashes in the new crash prevention areas of the app. |
| O1-KR2.t9 | O1-KR2 | 3 | O1-KR2.t8 | Monitor crash-free sessions again | Crash-free session data recorded in Firebase Analytics for the next 2 weeks. |
| O1-KR2.t10 | O1-KR2 | 4 | O1-KR2.t9 | Final analysis and report | Final analysis report confirming crash-free sessions have reached 99.5%. |
| O2-KR1.t1 | O2-KR1 | 3 | — | Define user growth strategy | A document with 5 growth tactics and their expected impact on MAU. |
| O2-KR1.t2 | O2-KR1 | 3 | O2-KR1.t1 | Research user acquisition channels | A list of 5 user acquisition channels with their cost and potential reach. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t1, O2-KR1.t2, O1-KR1.t8 | Create onboarding flow for new users | A wireframe or mockup of the onboarding flow with 3 key steps. |
| O2-KR1.t4 | O2-KR1 | 5 | O2-KR1.t3 | Implement referral program | A working referral system with a tracking dashboard and reward mechanism. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t3, O2-KR1.t4 | Run A/B test for onboarding flow | A report with A/B test results and recommendations for improvement. |
| O2-KR1.t6 | O2-KR1 | 3 | O2-KR1.t4, O2-KR1.t5 | Launch referral program | Referral program live with tracking metrics and user feedback. |
| O2-KR1.t7 | O2-KR1 | 3 | O2-KR1.t6 | Measure MAU growth | A report showing MAU growth and key performance indicators. |
| O2-KR2.t1 | O2-KR2 | 2 | — | Define rating improvement criteria | A document outlining the rating improvement criteria and target metrics is created. |
| O2-KR2.t2 | O2-KR2 | 3 | O2-KR2.t1 | Research current user feedback | A summary of user feedback and common issues is documented. |
| O2-KR2.t3 | O2-KR2 | 6 | O2-KR2.t2, O1-KR1.t8 | Implement rating improvement features | The core features are implemented and deployed to the app. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Refine features based on internal testing | A refined version of the features is ready for release. |
| O2-KR2.t5 | O2-KR2 | 4 | O2-KR2.t4 | Launch rating improvement campaign | A campaign is launched with in-app messages and social media posts. |
| O2-KR2.t6 | O2-KR2 | 6 | O2-KR2.t5 | Monitor and measure rating changes | A report showing the average store rating over time is created. |
| O3-KR1.t1 | O3-KR1 | 2 | — | Define conversion criteria and tools | Firebase conversion tracking setup complete with defined events and filters. |
| O3-KR1.t2 | O3-KR1 | 3 | O3-KR1.t1 | Analyze current conversion funnel | Conversion funnel analysis report with identified bottlenecks. |
| O3-KR1.t3 | O3-KR1 | 4 | O3-KR1.t2 | Design A/B test variants | Two pricing variant designs ready for testing. |
| O3-KR1.t4 | O3-KR1 | 6 | O3-KR1.t3 | Run A/B test with variants | A/B test results collected and stored in Firebase Analytics. |
| O3-KR1.t5 | O3-KR1 | 4 | O3-KR1.t4 | Review A/B test results | A/B test results analyzed and a decision memo drafted. |
| O3-KR1.t6 | O3-KR1 | 3 | O3-KR1.t5 | Implement the winning variant | Winning pricing variant implemented and live in the app. |
| O3-KR1.t7 | O3-KR1 | 4 | O3-KR1.t6 | Monitor conversion rate | Conversion rate tracked and reported for the quarter. |
| O3-KR2.t1 | O3-KR2 | 2 | — | Define pricing experiment variants | Two pricing models documented in a shared document. |
| O3-KR2.t2 | O3-KR2 | 3 | O3-KR2.t1 | Prepare pricing experiment setup | Experiment setup is ready with tracking tools and user segments. |
| O3-KR2.t3 | O3-KR2 | 4 | O3-KR2.t2 | Launch pricing experiment variant 1 | Variant 1 is live with a defined user segment. |
| O3-KR2.t4 | O3-KR2 | 4 | O3-KR2.t3 | Launch pricing experiment variant 2 | Variant 2 is live with a defined user segment. |
| O3-KR2.t5 | O3-KR2 | 6 | O3-KR2.t4 | Collect data from pricing experiment | Data collected for both variants in a shared spreadsheet. |
| O3-KR2.t6 | O3-KR2 | 4 | O3-KR2.t5 | Analyze pricing experiment results | Analysis report with key insights and metrics. |
| O3-KR2.t7 | O3-KR2 | 4 | O3-KR2.t6, O3-KR1.t7 | Write decision memo for pricing experiment | Decision memo with clear recommendation and rationale. |
| O3-KR2.t8 | O3-KR2 | 2 | — | Measure baseline for pricing experiment | Baseline metrics recorded in a shared document. |
| O3-KR2.t9 | O3-KR2 | 3 | O3-KR2.t8 | Track metrics during pricing experiment | Mid-quarter metrics recorded in a shared document. |
| O3-KR2.t10 | O3-KR2 | 2 | O3-KR2.t9 | Measure final results of pricing experiment | Final metrics recorded in a shared document. |

### Descriptions

- **O1-KR1.t1**: Clarify the features for streaks and smart reminders.
- **O1-KR1.t2**: Create the UI mockups for the new features.
- **O1-KR1.t3**: Write the code for tracking streaks in the app.
- **O1-KR1.t4**: Write the code for smart reminders based on user behavior.
- **O1-KR1.t5**: Test the new features with a group of internal users.
- **O1-KR1.t6**: Make changes to v2 based on user feedback.
- **O1-KR1.t7**: Prepare the app for submission to both app stores.
- **O1-KR1.t8**: Submit the app to both app stores for review.
- **O1-KR1.t9**: Track reviews and ratings after submission.
- **O1-KR2.t1**: Set up tools to track crash-free sessions and establish the current baseline.
- **O1-KR2.t2**: Review crash logs and user reports to find common causes of crashes.
- **O1-KR2.t3**: Implement fixes for the top 3 crash causes identified in the logs.
- **O1-KR2.t4**: Run unit and integration tests for the fixed crash areas.
- **O1-KR2.t5**: Track crash-free sessions in Firebase Analytics for the next 2 weeks.
- **O1-KR2.t6**: Review crash-free session data to assess progress toward the target of 99.5%.
- **O1-KR2.t7**: Add additional safeguards to prevent crashes in edge cases.
- **O1-KR2.t8**: Run unit and integration tests for the new crash prevention measures.
- **O1-KR2.t9**: Track crash-free sessions in Firebase Analytics for the next 2 weeks.
- **O1-KR2.t10**: Review crash-free session data to confirm the target of 99.5% is met.
- **O2-KR1.t1**: Outline tactics to increase MAU by 3,000.
- **O2-KR1.t2**: Identify and evaluate platforms for user growth.
- **O2-KR1.t3**: Design a user-friendly onboarding process to increase retention.
- **O2-KR1.t4**: Build a referral system to incentivize existing users to invite others.
- **O2-KR1.t5**: Test the onboarding flow with a sample of users to measure effectiveness.
- **O2-KR1.t6**: Deploy the referral program and monitor its performance.
- **O2-KR1.t7**: Track MAU growth over the quarter and compare to baseline.
- **O2-KR2.t1**: Set clear goals for what constitutes a 4.4 rating.
- **O2-KR2.t2**: Collect and analyze user reviews and ratings to identify common issues.
- **O2-KR2.t3**: Develop and deploy features that directly improve user satisfaction.
- **O2-KR2.t4**: Conduct internal testing and refine features based on feedback.
- **O2-KR2.t5**: Promote the new features to users through in-app messages and social media.
- **O2-KR2.t6**: Track the average store rating over time and compare it to the baseline.
- **O3-KR1.t1**: Set up tracking for free-to-paid conversion using Firebase Analytics.
- **O3-KR1.t2**: Review existing user flow and identify drop-off points in the conversion process.
- **O3-KR1.t3**: Create 2 pricing variant options for the free-to-paid conversion process.
- **O3-KR1.t4**: Implement and run the A/B test for the pricing variants over the next 4 weeks.
- **O3-KR1.t5**: Analyze the performance of each pricing variant and determine which one is more effective.
- **O3-KR1.t6**: Apply the most effective pricing variant to the free-to-paid conversion process.
- **O3-KR1.t7**: Track the free-to-paid conversion rate over the next 4 weeks to measure the impact.
- **O3-KR2.t1**: Set up two pricing models for the experiment.
- **O3-KR2.t2**: Set up the experiment with tools like Firebase or Google Sheets.
- **O3-KR2.t3**: Deploy the first pricing model to a segment of users.
- **O3-KR2.t4**: Deploy the second pricing model to a segment of users.
- **O3-KR2.t5**: Track user behavior, revenue, and engagement for both variants.
- **O3-KR2.t6**: Compare user behavior, revenue, and engagement between the two variants.
- **O3-KR2.t7**: Document the findings and recommend a pricing model.
- **O3-KR2.t8**: Record the current user behavior and revenue before the experiment.
- **O3-KR2.t9**: Monitor user behavior and revenue during the experiment.
- **O3-KR2.t10**: Record the final user behavior and revenue after the experiment.
