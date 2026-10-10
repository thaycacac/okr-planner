# Plan Mbec4 — sample 06_mobile_app_launch_en

- Pipeline status: `ok`

## Tasks (30 tasks, 122 h)

| id | kr | h | depends_on | title | done_criteria |
|---|---|---|---|---|---|
| O1-KR1.t1 | O1-KR1 | 4 | — | Design and implement streak tracking feature | Streak tracking feature is fully implemented and passes initial testing. |
| O1-KR1.t2 | O1-KR1 | 4 | — | Design and implement smart reminders feature | Smart reminders feature is fully implemented and passes initial testing. |
| O1-KR1.t3 | O1-KR1 | 4 | O1-KR1.t1, O1-KR1.t2 | Test and debug streaks and smart reminders features | Streaks and smart reminders features are fully tested and free of critical bugs. |
| O1-KR1.t4 | O1-KR1 | 4 | O1-KR1.t3 | Prepare app for release on App Store and Google Play | App is fully prepared for submission to App Store and Google Play, including all required metadata and assets. |
| O1-KR1.t5 | O1-KR1 | 2 | O1-KR1.t4 | Submit app to App Store and Google Play | App has been successfully submitted to App Store and Google Play and is awaiting approval. |
| O1-KR2.t1 | O1-KR2 | 4 | — | Analyze crash logs and identify root causes | A list of identified crash points with their root causes is documented and ready for prioritization. |
| O1-KR2.t2 | O1-KR2 | 2 | O1-KR2.t1 | Prioritize crash fixes based on impact and complexity | A prioritized list of crash fixes is created, with clear order of implementation. |
| O1-KR2.t3 | O1-KR2 | 6 | O1-KR2.t2 | Implement high-priority crash fixes | The highest-priority crash fixes are implemented, tested, and merged into the main codebase. |
| O1-KR2.t4 | O1-KR2 | 4 | O1-KR2.t3 | Conduct regression testing after crash fixes | Regression testing is completed, and no new issues are found that are related to the crash fixes. |
| O1-KR2.t5 | O1-KR2 | 2 | O1-KR2.t4 | Monitor crash-free sessions post-release | Crash-free session metrics are being monitored and logged for analysis. |
| O2-KR1.t1 | O2-KR1 | 4 | — | Research and identify growth strategies for increasing monthly active users | A list of 5-7 potential growth strategies is compiled and documented. |
| O2-KR1.t2 | O2-KR1 | 6 | O2-KR1.t1 | Design and implement a referral program for Habitly | The referral program is fully implemented and tested within the app. |
| O2-KR1.t3 | O2-KR1 | 4 | O2-KR1.t1 | Optimize onboarding experience for new users | The onboarding process is updated and tested with a small group of users. |
| O2-KR1.t4 | O2-KR1 | 4 | O2-KR1.t1 | Implement in-app engagement features to increase daily usage | The new in-app engagement features are implemented and tested. |
| O2-KR1.t5 | O2-KR1 | 4 | O2-KR1.t2, O2-KR1.t3, O2-KR1.t4 | Launch and monitor the referral program and onboarding improvements | The referral program and onboarding improvements are live and being monitored for impact. |
| O2-KR1.t6 | O2-KR1 | 4 | O2-KR1.t5 | Analyze user data and refine growth strategies | A report summarizing the analysis and recommendations for refining growth strategies is completed. |
| O2-KR2.t1 | O2-KR2 | 4 | — | Analyze current store ratings and user feedback | A comprehensive summary of current store ratings and user feedback is documented, highlighting key areas for improvement. |
| O2-KR2.t2 | O2-KR2 | 4 | O2-KR2.t1 | Develop and implement a user feedback collection system | The in-app feedback collection system is fully implemented and tested, with users able to provide feedback seamlessly. |
| O2-KR2.t3 | O2-KR2 | 6 | O2-KR2.t1, O2-KR2.t2 | Address common issues identified in user feedback | The most critical issues identified in user feedback have been resolved and verified to improve user satisfaction. |
| O2-KR2.t4 | O2-KR2 | 4 | O2-KR2.t3 | Implement a feature to encourage users to leave store ratings | The feature to encourage users to leave store ratings is fully implemented and integrated into the app. |
| O2-KR2.t5 | O2-KR2 | 4 | O2-KR2.t4 | Monitor and analyze the impact of implemented changes on store ratings | A detailed analysis of the impact of implemented changes on store ratings is completed, showing progress toward the target rating of 4.4. |
| O3-KR1.t1 | O3-KR1 | 4 | — | Analyze current free-to-paid conversion funnel | A detailed analysis report of the current free-to-paid conversion funnel is completed, highlighting key drop-off points and opportunities for improvement. |
| O3-KR1.t2 | O3-KR1 | 4 | O3-KR1.t1 | Design and implement a conversion optimization strategy | A conversion optimization strategy document is completed, outlining specific actions to be taken to improve the free-to-paid conversion rate. |
| O3-KR1.t3 | O3-KR1 | 4 | O3-KR1.t2 | Implement and test conversion improvements | All proposed conversion improvements are implemented and tested in a controlled environment, with no critical bugs or issues identified. |
| O3-KR1.t4 | O3-KR1 | 4 | O3-KR1.t3 | Monitor and evaluate the impact of conversion improvements | A report is generated showing the impact of the implemented conversion improvements on the free-to-paid conversion rate, including any measurable increase in the rate. |
| O3-KR1.t5 | O3-KR1 | 4 | O3-KR1.t4 | Refine and iterate based on performance data | A refined conversion strategy is completed, incorporating insights from performance data and outlining next steps for further optimization. |
| O3-KR2.t1 | O3-KR2 | 4 | — | Define pricing variants and hypothesis | Two pricing variants are clearly defined with a hypothesis and feature set documented. |
| O3-KR2.t2 | O3-KR2 | 6 | O3-KR2.t1 | Implement pricing experiment in app | The app is updated with the two pricing variants, and users are being randomly assigned to one of the variants. |
| O3-KR2.t3 | O3-KR2 | 4 | O3-KR2.t2 | Collect and analyze data from experiment | Data from the pricing experiment is collected and analyzed, with clear insights on which variant performed better. |
| O3-KR2.t4 | O3-KR2 | 4 | O3-KR2.t3 | Write decision memo based on experiment results | A written decision memo is completed, summarizing the experiment and its implications for Habitly's monetization strategy. |

### Descriptions

- **O1-KR1.t1**: Create the logic and UI for streak tracking, including how streaks are calculated, displayed, and updated based on user activity. Ensure the feature is fully functional and integrated with the existing app codebase.
- **O1-KR1.t2**: Develop the smart reminders feature, including user customization options, scheduling logic, and integration with Firebase for push notifications. Ensure the feature is fully functional and integrated with the existing app codebase.
- **O1-KR1.t3**: Perform thorough testing of the streaks and smart reminders features, including edge cases, user flows, and integration with Firebase. Fix any bugs or issues discovered during testing.
- **O1-KR1.t4**: Update app metadata, screenshots, and descriptions for both App Store and Google Play. Ensure the app meets all guidelines and requirements for submission. Prepare necessary documentation and assets.
- **O1-KR1.t5**: Submit the updated app to both App Store and Google Play. Monitor the submission process and address any feedback or issues raised by the app stores.
- **O1-KR2.t1**: Review crash logs from Firebase Crashlytics to identify the most frequent crash points and their root causes. Focus on understanding the context, frequency, and impact of each crash.
- **O1-KR2.t2**: Evaluate the identified crash points based on their impact on user experience, frequency, and complexity of resolution. Prioritize them for fixing in the next development cycle.
- **O1-KR2.t3**: Develop and implement fixes for the highest-priority crash points identified in the previous task. Ensure that the fixes are thoroughly tested and integrated into the codebase.
- **O1-KR2.t4**: Perform comprehensive regression testing to ensure that the implemented crash fixes have not introduced new issues or broken existing functionality.
- **O1-KR2.t5**: After releasing the updated version of the app, monitor crash-free sessions using Firebase Crashlytics to track progress toward the target of 99.5%.
- **O2-KR1.t1**: Conduct research on effective growth strategies for habit-tracking apps, including user acquisition, retention tactics, and referral programs. Analyze competitors and industry trends to identify opportunities for growth.
- **O2-KR1.t2**: Create a referral program that incentivizes existing users to invite new users. Develop the necessary backend and frontend features using Flutter and Firebase to support the program.
- **O2-KR1.t3**: Revise the onboarding process to improve user engagement and reduce early drop-offs. Implement changes in Flutter and Firebase to ensure a smoother and more effective onboarding flow.
- **O2-KR1.t4**: Add features such as daily reminders, progress tracking, and motivational messages to encourage users to engage with the app more frequently.
- **O2-KR1.t5**: Deploy the referral program and onboarding improvements to all users. Monitor user engagement and track the impact on monthly active users using Firebase analytics.
- **O2-KR1.t6**: Analyze user data from Firebase to assess the effectiveness of the referral program, onboarding improvements, and in-app engagement features. Use insights to refine and optimize growth strategies.
- **O2-KR2.t1**: Review existing store ratings and user feedback to identify common issues or areas for improvement. This includes analyzing app store reviews, user comments, and any other relevant feedback sources.
- **O2-KR2.t2**: Create an in-app feedback collection system to gather more detailed and structured user feedback. This includes designing prompts, integrating feedback forms, and ensuring the system is user-friendly.
- **O2-KR2.t3**: Based on the analysis from task t1, prioritize and address the most common issues reported by users. This may involve fixing bugs, improving app performance, or enhancing user experience features.
- **O2-KR2.t4**: Design and implement a feature that prompts users to leave store ratings after specific in-app actions, such as completing a habit streak or upgrading to a premium subscription. This includes designing the prompt and integrating it into the app.
- **O2-KR2.t5**: Track and analyze the effect of the implemented changes on the average store rating. This includes reviewing new user feedback, monitoring app store ratings, and comparing the results to the baseline.
- **O3-KR1.t1**: Review user behavior data from Firebase to identify where users are dropping off in the free-to-paid conversion funnel. This includes analyzing the flow from onboarding to the first paid conversion.
- **O3-KR1.t2**: Based on the analysis from the previous task, create a strategy to improve the free-to-paid conversion rate. This includes identifying specific features, messaging, or onboarding changes that could increase conversions.
- **O3-KR1.t3**: Implement the proposed conversion improvements in the Habitly app, such as updating onboarding flows, adding in-app prompts, or refining pricing messaging. Ensure all changes are tested in a controlled environment.
- **O3-KR1.t4**: Track the performance of the implemented changes over a defined period, comparing the free-to-paid conversion rate before and after the changes. Use Firebase analytics to measure the impact.
- **O3-KR1.t5**: Based on the results from the previous task, refine the conversion strategy and make any necessary adjustments to further improve the free-to-paid conversion rate. This may involve A/B testing additional variations or optimizing existing features.
- **O3-KR2.t1**: Create two distinct pricing variants for the Habitly app, including pricing tiers, features, and a clear hypothesis about how each variant will influence user behavior and conversion rates.
- **O3-KR2.t2**: Update the Habitly app with the two pricing variants, ensuring that users are randomly assigned to one of the variants and that the experiment is fully functional within the app.
- **O3-KR2.t3**: Run the pricing experiment for a sufficient period to collect meaningful data, then analyze the results to determine which pricing variant performs better in terms of conversion rates and user engagement.
- **O3-KR2.t4**: Draft a written decision memo summarizing the experiment's setup, results, and recommendations for the future pricing strategy of Habitly.
