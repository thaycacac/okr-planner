# Plan M3f57 — sample 06_mobile_app_launch_en

- Pipeline status: `ok`

## Tasks (58 tasks, 221 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Define release criteria and scope for v2 | A document outlining the release criteria and scope for v2 is finalized and shared with stakeholders. |
| O1-KR1.t2 | O1-KR1 | 3 | O1-KR1.t1 | Set up tools and templates for v2 development | All required tools and templates for v2 development are set up and ready for use. |
| O1-KR1.t3 | O1-KR1 | 5 | O1-KR1.t2 | Implement streak tracking feature | The streak tracking feature is fully implemented and passes initial unit tests. |
| O1-KR1.t4 | O1-KR1 | 5 | O1-KR1.t2 | Implement smart reminders feature | The smart reminders feature is fully implemented and passes initial unit tests. |
| O1-KR1.t5 | O1-KR1 | 4 | O1-KR1.t3, O1-KR1.t4 | Integrate streaks and smart reminders into the app | Streaks and smart reminders are fully integrated into the app and working as expected. |
| O1-KR1.t6 | O1-KR1 | 4 | O1-KR1.t5 | Test streaks and smart reminders features | All tests for streaks and smart reminders features are completed and passed successfully. |
| O1-KR1.t7 | O1-KR1 | 4 | O1-KR1.t6 | Fix bugs and optimize performance for v2 | All critical bugs and performance issues in v2 are resolved and the app is optimized. |
| O1-KR1.t8 | O1-KR1 | 3 | O1-KR1.t7 | Prepare app for release on App Store and Google Play | All materials for App Store and Google Play submission are prepared and ready for upload. |
| O1-KR1.t9 | O1-KR1 | 2 | O1-KR1.t8 | Submit app for review on App Store and Google Play | The v2 app has been successfully submitted for review on both App Store and Google Play. |
| O1-KR1.t10 | O1-KR1 | 3 | O1-KR1.t9 | Monitor app store reviews and address feedback | All initial feedback from App Store and Google Play is reviewed and addressed. |
| O1-KR1.t11 | O1-KR1 | 2 | O1-KR1.t10 | Release v2 on App Store and Google Play | The v2 app is live on both App Store and Google Play. |
| O1-KR1.t12 | O1-KR1 | 3 | O1-KR1.t11 | Measure user engagement with v2 features | Initial user engagement metrics for v2 features are collected and analyzed. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Analyze crash logs and identify root causes | List of top 3 crash points with initial analysis of their causes |
| O1-KR2.t2 | O1-KR2 | 3 | O1-KR2.t1 | Prioritize crash fixes based on impact and complexity | Prioritized list of crash fixes with estimated effort and impact |
| O1-KR2.t3 | O1-KR2 | 6 | O1-KR2.t2 | Implement high-impact crash fixes | Code changes merged into the main branch for the top 2 crash fixes |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Test crash fixes in staging environment | Test results confirming that the top 2 crash fixes are resolved in staging |
| O1-KR2.t5 | O1-KR2 | 3 | O1-KR2.t4 | Deploy crash fixes to production | Crash fixes deployed to production and confirmed live in the app |
| O1-KR2.t6 | O1-KR2 | 2 | O1-KR2.t5 | Monitor crash-free sessions post-deployment | Crash-free sessions metric updated in Firebase dashboard post-deployment |
| O1-KR2.t7 | O1-KR2 | 2 | — | Measure baseline crash-free sessions metric | Baseline crash-free sessions metric documented in a spreadsheet or note |
| O1-KR2.t8 | O1-KR2 | 2 | O1-KR2.t7 | Mid-quarter check of crash-free sessions metric | Mid-quarter crash-free sessions metric documented in a spreadsheet or note |
| O1-KR2.t9 | O1-KR2 | 2 | O1-KR2.t8 | Final check of crash-free sessions metric | Final crash-free sessions metric documented in a spreadsheet or note |
| O2-KR1.t1 | O2-KR1 | 4 | — | Define growth strategy and set user acquisition goals | A written growth strategy document with clear goals and tactics is produced and reviewed by the developer. |
| O2-KR1.t2 | O2-KR1 | 4 | O2-KR1.t1 | Research and identify top user acquisition channels | A list of top user acquisition channels with brief descriptions and potential impact is produced. |
| O2-KR1.t3 | O2-KR1 | 6 | O2-KR1.t2 | Design and implement a referral program | The referral program is fully implemented and live in the app with a clear user interface and incentive structure. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t2 | Optimize app store listings and metadata | App store listings are updated with optimized titles, descriptions, and visuals, and the changes are live. |
| O2-KR1.t5 | O2-KR1 | 6 | O2-KR1.t2 | Create and publish marketing content for social media and blogs | A minimum of 10 marketing posts and 3 blog articles are published across relevant social media platforms and the company blog. |
| O2-KR1.t6 | O2-KR1 | 6 | O2-KR1.t2, O2-KR1.t5, O1-KR1.t11 | Implement and launch a social media campaign | The social media campaign is fully launched with clear objectives, targeting, and content schedule. |
| O2-KR1.t7 | O2-KR1 | 4 | O2-KR1.t3, O2-KR1.t4, O2-KR1.t6 | Analyze and track user acquisition sources | Analytics tools are configured and user acquisition sources are being tracked with clear metrics. |
| O2-KR1.t8 | O2-KR1 | 4 | O2-KR1.t7 | Review and optimize user acquisition strategy based on early results | A review report with findings and recommendations for optimizing the user acquisition strategy is produced. |
| O2-KR1.t9 | O2-KR1 | 6 | O2-KR1.t8 | Scale successful user acquisition tactics | At least two successful user acquisition tactics are scaled and their impact is being tracked. |
| O2-KR1.t10 | O2-KR1 | 4 | O2-KR1.t9 | Measure and report on monthly active users growth | A final report on monthly active users growth is produced, showing the achieved number and progress toward the target. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Analyze current store ratings and feedback | A summary document of current store ratings and user feedback is created. |
| O2-KR2.t2 | O2-KR2 | 3 | O2-KR2.t1 | Define improvement criteria and action plan | A written action plan for improving store ratings is finalized. |
| O2-KR2.t3 | O2-KR2 | 5 | O2-KR2.t2 | Implement in-app prompts for user reviews | In-app prompts for user reviews are implemented and tested. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Test in-app prompts with a small user group | Feedback from a small user group on the in-app prompts is collected and documented. |
| O2-KR2.t5 | O2-KR2 | 3 | O2-KR2.t4 | Revise in-app prompts based on feedback | Revised in-app prompts are implemented and ready for full rollout. |
| O2-KR2.t6 | O2-KR2 | 3 | O2-KR2.t5 | Roll out revised in-app prompts to all users | The revised in-app prompts are live and accessible to all users. |
| O2-KR2.t7 | O2-KR2 | 3 | O2-KR2.t6 | Monitor and track store ratings over time | A system is in place to track store ratings and user feedback over time. |
| O2-KR2.t8 | O2-KR2 | 3 | O2-KR2.t7 | Collect mid-quarter store rating data | Mid-quarter store rating data is collected and stored in a spreadsheet with the average rating calculated. |
| O2-KR2.t9 | O2-KR2 | 3 | O2-KR2.t8 | Collect end-of-quarter store rating data | End-of-quarter store rating data is collected and stored in a spreadsheet with the average rating calculated. |
| O2-KR2.t10 | O2-KR2 | 4 | O2-KR2.t9 | Prepare a report on rating improvements | A report on the improvements in store ratings is finalized and ready for review. |
| O3-KR1.t1 | O3-KR1 | 3 | — | Define free-to-paid conversion criteria and baseline | Conversion criteria and baseline documented in a shared file. |
| O3-KR1.t2 | O3-KR1 | 4 | O3-KR1.t1 | Analyze current user behavior and conversion funnel | Conversion funnel analysis completed and saved in a shared file. |
| O3-KR1.t3 | O3-KR1 | 4 | O3-KR1.t2 | Design A/B test for free-to-paid conversion | Test plan with variations documented in a shared file. |
| O3-KR1.t4 | O3-KR1 | 6 | O3-KR1.t3 | Implement A/B test in Habitly | A/B test fully implemented and running in the app. |
| O3-KR1.t5 | O3-KR1 | 4 | O3-KR1.t4 | Monitor A/B test performance | Test performance data collected and saved in a shared file. |
| O3-KR1.t6 | O3-KR1 | 4 | O3-KR1.t5 | Review A/B test results and identify improvements | Test results reviewed and improvements identified in a shared file. |
| O3-KR1.t7 | O3-KR1 | 6 | O3-KR1.t6 | Implement improvements from A/B test | Improvements from A/B test implemented and live in the app. |
| O3-KR1.t8 | O3-KR1 | 4 | O3-KR1.t7 | Measure free-to-paid conversion rate post-improvements | Conversion rate data collected and saved in a shared file. |
| O3-KR1.t9 | O3-KR1 | 3 | O3-KR1.t8 | Compare baseline and final conversion rates | Comparison of baseline and final conversion rates documented in a shared file. |
| O3-KR2.t1 | O3-KR2 | 3 | O3-KR1.t9 | Define pricing experiment criteria and scope | A document outlining the experiment's objectives, success metrics, and scope is created and reviewed. |
| O3-KR2.t2 | O3-KR2 | 4 | O3-KR2.t1 | Design pricing variants and experiment setup | A document with the two pricing variants and the experiment setup is finalized and reviewed. |
| O3-KR2.t3 | O3-KR2 | 5 | O3-KR2.t2 | Implement pricing experiment in Firebase | The pricing experiment is fully implemented and running in Firebase with user tracking enabled. |
| O3-KR2.t4 | O3-KR2 | 3 | O3-KR2.t3 | Collect baseline data for pricing experiment | A report with baseline data for the pricing experiment is created and reviewed. |
| O3-KR2.t5 | O3-KR2 | 4 | O3-KR2.t4 | Run pricing experiment for 3 weeks | Data from the 3-week pricing experiment is collected and stored in Firebase. |
| O3-KR2.t6 | O3-KR2 | 4 | O3-KR2.t5 | Analyze pricing experiment results | A report with the analysis of the pricing experiment results is created and reviewed. |
| O3-KR2.t7 | O3-KR2 | 4 | O3-KR2.t6 | Write decision memo based on experiment results | A decision memo is written and reviewed, summarizing the pricing experiment results and recommendations. |
| O3-KR2.t8 | O3-KR2 | 3 | O3-KR2.t7 | Review and finalize decision memo | The decision memo is finalized and approved for submission. |

### Descriptions

- **O1-KR1.t1**: Establish the features, quality standards, and deliverables for v2, including streaks and smart reminders.
- **O1-KR1.t2**: Prepare necessary tools, code templates, and documentation for building v2 features.
- **O1-KR1.t3**: Develop the core functionality for streak tracking in the app.
- **O1-KR1.t4**: Develop the core functionality for smart reminders in the app.
- **O1-KR1.t5**: Combine the streaks and smart reminders features into the existing app codebase.
- **O1-KR1.t6**: Conduct thorough testing of the streaks and smart reminders features to ensure they are stable and functional.
- **O1-KR1.t7**: Identify and resolve any bugs or performance issues in the v2 features.
- **O1-KR1.t8**: Finalize app metadata, screenshots, and other materials required for release on both app stores.
- **O1-KR1.t9**: Submit the v2 app for review on both App Store and Google Play.
- **O1-KR1.t10**: Monitor feedback from App Store and Google Play and address any issues that arise.
- **O1-KR1.t11**: Publish the v2 app on both App Store and Google Play after approval.
- **O1-KR1.t12**: Track user engagement with streaks and smart reminders features post-release.
- **O1-KR2.t1**: Review crash logs from Firebase Crashlytics to identify the most frequent crash points and their root causes.
- **O1-KR2.t2**: Rank the identified crash issues based on their impact on user experience and the complexity of fixing them.
- **O1-KR2.t3**: Develop and implement fixes for the highest-priority crash issues identified in the analysis.
- **O1-KR2.t4**: Deploy the implemented crash fixes to the staging environment and run automated and manual tests to ensure they resolve the issues.
- **O1-KR2.t5**: Release the tested crash fixes to the production environment through Firebase and ensure they are live.
- **O1-KR2.t6**: Track the crash-free sessions metric in Firebase after deploying the fixes to ensure improvement.
- **O1-KR2.t7**: Record the current crash-free sessions metric as a baseline for comparison.
- **O1-KR2.t8**: Review the crash-free sessions metric halfway through the quarter to assess progress.
- **O1-KR2.t9**: Review the crash-free sessions metric at the end of the quarter to determine if the target was met.
- **O2-KR1.t1**: Create a detailed plan for growing monthly active users, including target channels, tactics, and KPIs.
- **O2-KR1.t2**: Investigate and list the most effective channels for acquiring new users, such as social media, app store optimization, and referral programs.
- **O2-KR1.t3**: Create and launch a referral program to encourage existing users to invite others to the app.
- **O2-KR1.t4**: Improve the app store listing for both App Store and Google Play to increase visibility and conversion rates.
- **O2-KR1.t5**: Develop and publish a series of marketing posts and blog articles to drive traffic and awareness for the app.
- **O2-KR1.t6**: Launch a targeted social media campaign to attract new users and increase app visibility.
- **O2-KR1.t7**: Set up analytics tools to track the performance of different user acquisition channels and campaigns.
- **O2-KR1.t8**: Analyze early performance data and make adjustments to the user acquisition strategy for better results.
- **O2-KR1.t9**: Expand and scale the most effective user acquisition tactics identified during the quarter.
- **O2-KR1.t10**: Track and report on the growth of monthly active users at the end of the quarter to assess progress toward the target.
- **O2-KR2.t1**: Review existing store ratings and user feedback to identify areas for improvement.
- **O2-KR2.t2**: Create a plan for improving store ratings based on the analysis.
- **O2-KR2.t3**: Develop and integrate in-app prompts that encourage users to leave reviews.
- **O2-KR2.t4**: Run a small-scale test of the in-app prompts to gather feedback.
- **O2-KR2.t5**: Refine the in-app prompts based on the feedback from the test.
- **O2-KR2.t6**: Deploy the revised in-app prompts to all users across the app.
- **O2-KR2.t7**: Set up tracking mechanisms to monitor changes in store ratings.
- **O2-KR2.t8**: Gather and analyze store rating data halfway through the quarter.
- **O2-KR2.t9**: Gather and analyze store rating data at the end of the quarter.
- **O2-KR2.t10**: Compile a report summarizing the improvements in store ratings.
- **O3-KR1.t1**: Establish the current conversion rate and define what constitutes a successful conversion.
- **O3-KR1.t2**: Review analytics data to identify where users drop off before converting to paid.
- **O3-KR1.t3**: Create a test plan with variations to improve conversion rate.
- **O3-KR1.t4**: Set up the A/B test in the app using Firebase and Flutter.
- **O3-KR1.t5**: Track and analyze the performance of the A/B test over time.
- **O3-KR1.t6**: Analyze the test results to determine which variation performed best.
- **O3-KR1.t7**: Apply the best-performing changes to the app to improve free-to-paid conversion.
- **O3-KR1.t8**: Track the free-to-paid conversion rate after implementing the improvements.
- **O3-KR1.t9**: Compare the initial baseline conversion rate with the final rate after improvements.
- **O3-KR2.t1**: Establish the goals, metrics, and success criteria for the two-variant pricing experiment.
- **O3-KR2.t2**: Create the two pricing variants and outline the experiment setup, including user segmentation and control groups.
- **O3-KR2.t3**: Set up the pricing experiment in Firebase, including A/B testing and user tracking.
- **O3-KR2.t4**: Gather and document baseline metrics before the experiment begins.
- **O3-KR2.t5**: Monitor and collect data from the pricing experiment over a 3-week period.
- **O3-KR2.t6**: Analyze the collected data to determine the impact of the two pricing variants.
- **O3-KR2.t7**: Draft a written decision memo summarizing the findings and recommending a course of action.
- **O3-KR2.t8**: Finalize the decision memo based on feedback and ensure it is ready for submission.
