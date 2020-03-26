Workflow Development
====================

The steps to develop and test an SDP workflow are as follows:

- Clone the sdp-prototype repository from GitLab and create a new branch for
  your work.

- Create a directory for your workflow in ``src/workflows``:

  .. code-block::

    $ mkdir src/workflows/<my-workflow>
    $ cd src/workflows/<my-workflow>

- Write the workflow script (``<my-workflow>.py``). See the existing workflows
  for examples of how to do this.

- Create a ``Dockerfile`` for building the workflow image, e.g.

  .. code-block::

    FROM python:3.7

    RUN pip install ska_sdp_config

    WORKDIR /app
    COPY <my-workflow>.py .
    ENTRYPOINT ["python", "<my-workflow>.py"]

- Create a file called ``version.txt`` containing the semantic version number of
  the workflow.

- Create a ``Makefile`` containing

  .. code-block::

    NAME := workflow-<my-workflow>
    VERSION := $(shell cat version.txt)

    include ../../make/Makefile

- Build the workflow image:

  .. code-block::

    $ make build

- Push the image to the Nexus repository:

  .. code-block::

    $ make push

- Add the workflow to the workflow definition file
  ``src/workflows/workflows.json``.

- Commit the changes to your branch and push to GitLab.

- You can then test the workflow by starting SDP with the processing
  controller workflows URL pointing to your branch in GitLab:

    .. code-block::

      $ helm install sdp-prototype -n sdp-prototype \
        --set processing_controller.workflows.url=https://gitlab.com/ska-telescope/sdp-prototype/raw/<my-branch>/src/workflows/workflows.json

- Then create a processing block to run the workflow, either via the Tango
  interface, or by creating it directly in the config DB with ``sdpcfg``.


Additional steps to build a custom execution engine
---------------------------------------------------

If you want to use a custom execution engine (EE) in your workflow, the
additional steps you need to do are:

- Create a directory in ``src`` for your EE.

- Add the EE code.

- Build the EE Docker image(s) and push it/them to the Nexus repository.

- Add a Helm chart to deploy the EE containers in ``src/helm_deploy/charts``.

- Add the custom EE deployment to the workflow script.

- Commit changes to your branch and push to GitLab.

- When testing, you also need to point the Helm deployer to your branch of the
  repository:

  .. code-block::

    $ helm install sdp-prototype -n sdp-prototype \
      --set processing_controller.workflows.url=https://gitlab.com/ska-telescope/sdp-prototype/raw/<my-branch>/src/workflows/workflows.json \
      --set helm_deploy.chart_repo.ref=<my-branch>
