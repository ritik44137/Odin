# Bundle Plan Rubric

A strong bundle plan should be specific enough that an author could implement the ZIP without inventing major missing pieces.

## Minimum bar

A credible plan should clearly describe:

- what each required file will contain
- how the verifier will measure the actual objective
- how the oracle will solve the task
- what is visible to the agent versus hidden for grading
- how the draft's resources and network posture map into `task.toml`

## Signs of a weak bundle plan

A weak plan usually has one or more of these problems:

- it restates the draft without turning it into executable bundle design
- it names required files but does not explain what goes inside them
- it does not separate visible and hidden verification
- it has no real oracle story
- it ignores exploit paths
- it leaves resource or network posture ambiguous

## Self-check questions

- Could another engineer implement the bundle from this plan alone?
- Would the planned verifier still measure the real objective under hidden cases?
- Does the plan imply a realistic starting state in `/app`?
- Is the oracle path concrete enough to believe the task is solvable?
- Are early rejection points already addressed?