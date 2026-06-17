# Questions

## Q-001 Approve the proposed 4-topic backlog slicing (T1 v8-gap-analysis, T2 v8-gap-implementation, T3 p53-mdm2-infra-extraction, T4 cpp-build-revival) and dependency order before any are scaffolded with wkas init? See 00-state_of_project_v0.md 'Proposed Topic Slicing'.
*asked: cycle-0*
*priority: soft*
*answer:* 
We merge T1 and T2 because the audit of the gap analysis will be logically followed by a roadmap-described implementation path. T3 is the next research question which will be tackled as soon as we decide whether to pursue the merger T1+T2. So the dependency is real. T3 does not need to know about the details of T1+T2; simply I, the PI, will decide when to move on. You can drop T4 entirely for the near to intermediate future. We focus on building examples and learning from them. Then if everything goes well the schema will arise from the work. — PI, 2026-06-17
## Q-002 Should cpp-build-revival (T4: drop vcpkg from CMakePresets+CI, robust TBB detection, validate doc build) run in parallel now, or wait until the Python demo backlog (T1-T3) lands? It is independent but gates all future C++ Phase-2 schema work.
*asked: cycle-0*
*priority: soft*
*answer:* Drop T4 for now — PI, 2026-06-17
## Q-003 Reconciliation aggressiveness: I archived only the 3 fully-superseded reports (02/03/05) and kept 04/06-10. Do you want a follow-up pass to migrate doc-10's working code samples into examples/ and then archive doc-10 too?
*asked: cycle-0*
*priority: soft*
*answer:* The question is more about the value they bring to the series ofLLM-agents that will perform the work cycles. If they are useless, you drop. Otherwise, you keep. But as I remember the point of these documents was to try to avoid having to rely on `context7` calls every time because LLMs from 4 months ago had many difficulties with OpenUSD concepts. The point is rather than we need to find a way to get easy and cheap documentation access. — PI, 2026-06-17

