# Interface Management for the Bug Report Evaluator

The project team builds one system, divided into four subsystems. An **interface** is a boundary where two subsystems interact. **Interface management** is the systems engineering practice of identifying every interface, defining each one in writing, controlling changes to those definitions, and verifying that each subsystem meets them. This page explains how our team does that. For how industry and NASA teams approach it, see [Section 6.3, Interface Management](https://www.nasa.gov/reference/6-3-interface-management/), in the NASA Systems Engineering Handbook.

Each interface is defined in an interface agreement, using the [Interface Agreement Template](https://invisible-work-initiative.github.io/resources/interface-agreement/) on the Invisible Work Initiative website.

## Roles

- **The two subsystems on an interface** write its agreement together and own its content. Each agreement names one owner from each subsystem.
- **The Integration subsystem coordinates.** The Integration subsystem passes information between the other subsystems, so it is one of the two subsystems on most interfaces. In industry, a group called an interface working group usually does this coordination. For our team, the Integration subsystem keeps a current list of the system's interfaces and their agreements, brings together the subsystems that need to agree on an interface, and points out agreements that are missing or out of date. It does not write other subsystems' agreements for them.

## Identify the interfaces

The Integration subsystem leads the team in listing every place where two subsystems interact. A common tool for this is an N² diagram (read "N-squared"): a grid with the subsystems listed down the diagonal, where each off-diagonal cell records what one subsystem provides to another. An empty cell means those two subsystems do not interact directly.

## Define each interface

For each interface on the list, the two subsystems fill out the interface agreement template together. The agreement takes effect when both owners approve the pull request that adds it to this repository.

## Control changes

- Every change to an approved agreement is a pull request that both owners approve. Neither subsystem changes an approved interface on its own.
- When an agreement changes, both subsystems on that interface say so in their weekly updates in the `#bugs26` channel on Slack, and tag the members of the other subsystem.

## Verify each interface

- Each agreement's Verification section says how the two subsystems will show that they meet each interface requirement.
- Before each gate review, every interface your subsystem is part of has an agreement that both owners have approved. See the [Gate Review Checklist](https://invisible-work-initiative.github.io/resources/gate-review-checklist/).

## Organize the agreements

The team decides where in this repository to keep the agreements and the interface list, and how to name the files. Record that decision in a [decision record](https://invisible-work-initiative.github.io/resources/decision-record/) so that everyone can find them.
