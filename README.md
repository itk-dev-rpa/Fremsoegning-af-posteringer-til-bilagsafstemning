# Fremsøgning af posteringer til bilagsafstemning

## Intro

This robot is used to enrich a list of bilag with info in OPUS Sap.

The robot is activated by filling out a form in OS2Forms. This generates an email that is sent to the robot.
The robot takes the info from the email and sends the result back to the original sender.

The robot expects a list of whitelisted case workers who are allowed to activate the robot.
The whitelist should be given as a semicolon-separated list of az-ids.
This is given as the process arguments in OpenOrchestrator.

## Flow

The linear framework is used when a robot is just going from A to Z without fetching jobs from an
OpenOrchestrator queue.
The flow of the linear framework is sketched up in the following illustration:

![Linear Flow diagram](Robot-Framework.svg)

## Linting and Github Actions

This template is also setup with flake8 and pylint linting in Github Actions.
This workflow will trigger whenever you push your code to Github.
The workflow is defined under `.github/workflows/Linting.yml`.

