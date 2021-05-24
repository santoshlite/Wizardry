# Contributor's Guide

Welcome and thank you for your interest in contributing to Wizardry open source project.  This document aims to describe the preferred workflow contributors should follow when contributing new source code to the project. This Git workflow is inspired greatly by the [irON-Parsers Contributors Guide](https://github.com/structureddynamics/irON-Parsers/wiki/Collaboration%3A-git-development-workflow).

# Contributing

## Who is a Collaborator?

A collaborator is someone with write access to the Wizardry repository. Collaborators merge pull requests from contributors.

## Who is a Contributor?

A contributor can be anyone! It could be you. Continue reading this section if you wish to get involved and contribute back to the Wizardry open source project!

## Code Style and Testing

Code reviewers will be expecting to see code that follows Python guidelines.

## Initial Setup

* Setup a [GitHub](https://github.com/) account
* [Fork](https://help.github.com/articles/fork-a-repo/) the [repository](https://github.com/ssantoshp/Wizardry) of the project
* Clone your fork locally

```bash
$ git clone https://github.com/ssantoshp/Wizardry.git
```

* Navigate to the Wizardry directory and add the upstream remote

```bash
$ cd Lean
$ git remote add upstream https://github.com/ssantoshp/Wizardry.git
```

The remote upstream branch links your fork of Wizardry with our master copy, so when you perform a `git pull --rebase` you'll be getting updates from our repository.

## Keeping your master up-to-date!
Now that you've defined the `remote upstream branch`, you can refresh your local copy of master with the following commands:

```bash
$ git checkout master
$ git pull --rebase
```
