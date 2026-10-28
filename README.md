# Bug Report Evaluator

An automated quality checker for incoming bug reports on open source projects, built by the Bugs26 team in Cornell University's Systems Engineering Program, as part of the [Invisible Work Initiative](https://invisible-work-initiative.github.io).

Start with the [statement of work](https://invisible-work-initiative.github.io/projects/ai-and-open-source-bug-reports/) for what the system must do and how the course works. This page covers how our team works day to day.

## Documents

Where a new document goes: [where to put documents](documentation/README.md).

- [System requirements (draft)](documentation/system-requirements.md)
- [Interface management](documentation/interface-agreements.md)
- [Branch rules for `main`](.github/rulesets/README.md)

## The team

Our team name is Bugs26. You will see it on GitHub and in Slack. The team is divided into subsystems:

| Subsystem | Responsible engineers | Slack channel | Folder |
|---|---|---|---|
| Software Systems | Raveena, Zhouran | `#bugs26-systems` | [software-systems](documentation/subsystems/software-systems/) |
| Input Evaluation | Julian, Lurui | `#bugs26-evaluators` | [input-evaluation](documentation/subsystems/input-evaluation/) |
| Claim Investigation | Boyu, Qinyue | `#bugs26-investigators` | [claim-investigation](documentation/subsystems/claim-investigation/) |
| Integration | Andy, Meshaal | `#bugs26-integrators` | [integration](documentation/subsystems/integration/) |
| Writing | Raveena, Andy | `#bugs26-writers` | Writes in the folders above |

## Meetings

- Each subsystem meets with John for 30 minutes every week. The Writing subsystem meets every two weeks. John sends the invitations.
- Check-ins are for your questions, not for proving progress.
- Gate reviews happen twice each semester, on Zoom, and everyone attends.
- There are no other whole-team meetings. Meet your own subsystem, or another subsystem, as often as you find useful. Once a week or more within your subsystem is a good starting point. Rehearse for gate reviews on your own schedule.

## Weekly updates

Each subsystem posts a short written update in `#bugs26` every week, before its check-in. These updates are how subsystems keep each other informed between gate reviews, and each one is the agenda for that subsystem's check-in.

- Use the [weekly update template](https://invisible-work-initiative.github.io/resources/weekly-update/).
- Keep it under 150 words: Finished, Next, Blocked, Interface changes, Requests.

## Deliverables

**Gate reviews.** Four presentations across the year, which form most of your grade. See the [grading criteria](https://invisible-work-initiative.github.io/projects/ai-and-open-source-bug-reports/) and the [gate review checklist](https://invisible-work-initiative.github.io/resources/gate-review-checklist/).

| Gate | Date | What you present |
|---|---|---|
| Gate 1: Architecture | October 12 | Draft ConOps. Revised system requirements and draft subsystem requirements, with verification methods, tests, and draft interface agreements. |
| Gate 2: Alpha Prototype | December 7 | A poorly working system that takes in a report, evaluates it, investigates it, and returns something to the maintainer. Finished ConOps, draft system tests, finished interface agreements. |
| Gate 3: Beta Prototype | March 15 | A buggy but functioning system with measurable improvement on the system tests. Works on multiple inputs and returns meaningful outputs. |
| Gate 4: Operational System | May 3 | Full historical evaluation across at least three open source projects that differ in size and application domain, fully passing requirements and validated by industry experts. |

**Weekly written updates.** To each other, as described above.

**Interface agreements.** To each other. Write one with every subsystem that yours interacts with. Name one owner from each subsystem, and have both owners approve the pull request. Draft agreements are due at Gate 1 and finished agreements at Gate 2. The [interface management page](documentation/interface-agreements.md) explains the process, and the [template](https://invisible-work-initiative.github.io/resources/interface-agreement/) is on the website.

**The operational system.** Due at Gate 4. It must address the problem described in the statement of work.

## Working in this repository

- Do your work on a branch. `main` is protected.
- Open a pull request, get one teammate's approval, then merge. You cannot approve your own pull request.
- New commits clear earlier approvals, so resolve all comments before merging.
- [The branch rules](.github/rulesets/README.md) describe exactly what is enforced.
- New to GitHub or to open source? Read the [Open Resource Library](https://www.openresourcelibrary.com/), curated by colleagues at the University of Vermont.

## How we work

- Be kind to each other.
- Expect 10 to 15 hours per week for 3 credits, or 15 to 20 hours for 4 credits. Reading, meeting, and discussing count as work.
- The three-day rule: if something has blocked you for three days, ask for help.
- AI tools are expected. You are accountable for everything you submit.
- Write a [decision record](https://invisible-work-initiative.github.io/resources/decision-record/) for every decision worth remembering.
- Each subsystem writes its own [working agreement](https://invisible-work-initiative.github.io/resources/working-agreement/).
- Put interface agreements, decision records, and working agreements where [this page](documentation/README.md) says.

## Joining

1. If you are not yet in the GitHub organization, send John your GitHub username, or your Cornell NetID if you do not have an account yet.
2. Accept the invitation John sends, which adds you to the Bugs26 team.
3. Join Slack: [https://join.slack.com/t/invisiblework/shared_invite/zt-4a6adzuvq-RAxIdcb7qvcpiEohTg4rXw](https://join.slack.com/t/invisiblework/shared_invite/zt-4a6adzuvq-RAxIdcb7qvcpiEohTg4rXw)
4. Finish onboarding with a pull request to `CONTRIBUTORS.md` in the [onboarding repository](https://github.com/invisible-work-initiative/onboarding).
5. Write your subsystem's working agreement in your [subsystem folder](documentation/README.md).
6. Post your first weekly update.
