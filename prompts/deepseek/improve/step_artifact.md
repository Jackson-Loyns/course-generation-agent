请在不破坏当前步骤边界的前提下，根据以下改进要求修订“{step_label}”这一个步骤的 Markdown 产物。

只返回修订后的完整 Markdown。

硬约束：
1. 只允许修订当前步骤产物
2. 不得擅自改前序已确认步骤设定
3. 必须严格执行所有约束，尤其是用户明确排除的内容
4. 必须基于原稿做出可见的新变化

课程上下文：
{context_summary}

当前步骤可参考的前序已确认产物：
{prior_step_artifacts}

基础版本：
v{source_version}

本轮修订目标：
{revision_goal}

必须遵守的约束：
{constraint_summary}

改进要求：
{approved_changes}

当前 Markdown：
{markdown}
