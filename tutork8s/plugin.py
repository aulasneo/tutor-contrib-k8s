import os
from glob import glob

import importlib_resources
from tutor import hooks

from .__about__ import __version__

########################################
# CONFIGURATION
########################################

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Add your new settings that have default values here.
        # Each new setting is a pair: (setting_name, default_value).
        # Prefix your setting names with 'K8S_'.
        ("K8S_VERSION", __version__),
        # HPA settings
        ("K8S_LMS_HPA_ENABLE", True),
        ("K8S_LMS_HPA_CPU_ENABLE", False),
        ("K8S_LMS_HPA_MEMORY_ENABLE", True),
        ("K8S_LMS_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_LMS_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_LMS_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_LMS_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_LMS_HPA_SCALE_UP_PODS", 4),
        ("K8S_LMS_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_LMS_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_LMS_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_LMS_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_LMS_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # CMS HPA settings
        ("K8S_CMS_HPA_ENABLE", True),
        ("K8S_CMS_HPA_CPU_ENABLE", False),
        ("K8S_CMS_HPA_MEMORY_ENABLE", True),
        ("K8S_CMS_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_CMS_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_CMS_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_CMS_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_CMS_HPA_SCALE_UP_PODS", 4),
        ("K8S_CMS_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_CMS_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_CMS_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_CMS_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_CMS_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # LMS Worker HPA settings
        ("K8S_LMS_WORKER_HPA_ENABLE", True),
        ("K8S_LMS_WORKER_HPA_CPU_ENABLE", False),
        ("K8S_LMS_WORKER_HPA_MEMORY_ENABLE", True),
        ("K8S_LMS_WORKER_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_LMS_WORKER_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_LMS_WORKER_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_LMS_WORKER_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_LMS_WORKER_HPA_SCALE_UP_PODS", 4),
        ("K8S_LMS_WORKER_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_LMS_WORKER_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_LMS_WORKER_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_LMS_WORKER_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_LMS_WORKER_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # CMS Worker HPA settings
        ("K8S_CMS_WORKER_HPA_ENABLE", True),
        ("K8S_CMS_WORKER_HPA_CPU_ENABLE", False),
        ("K8S_CMS_WORKER_HPA_MEMORY_ENABLE", True),
        ("K8S_CMS_WORKER_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_CMS_WORKER_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_CMS_WORKER_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_CMS_WORKER_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_CMS_WORKER_HPA_SCALE_UP_PODS", 4),
        ("K8S_CMS_WORKER_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_CMS_WORKER_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_CMS_WORKER_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_CMS_WORKER_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_CMS_WORKER_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # MFE HPA settings
        ("K8S_MFE_HPA_ENABLE", True),
        ("K8S_MFE_HPA_CPU_ENABLE", False),
        ("K8S_MFE_HPA_MEMORY_ENABLE", True),
        ("K8S_MFE_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_MFE_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_MFE_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_MFE_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_MFE_HPA_SCALE_UP_PODS", 4),
        ("K8S_MFE_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_MFE_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_MFE_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_MFE_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_MFE_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # Caddy HPA settings
        ("K8S_CADDY_HPA_ENABLE", True),
        ("K8S_CADDY_HPA_CPU_ENABLE", False),
        ("K8S_CADDY_HPA_MEMORY_ENABLE", True),
        ("K8S_CADDY_HPA_CPU_AVERAGE_UTILIZATION", 80),
        ("K8S_CADDY_HPA_MEMORY_AVERAGE_UTILIZATION", 80),
        ("K8S_CADDY_HPA_SCALE_UP_STABILIZATION_WINDOW_SECONDS", 0),
        ("K8S_CADDY_HPA_SCALE_UP_PERCENT", 100),
        ("K8S_CADDY_HPA_SCALE_UP_PODS", 4),
        ("K8S_CADDY_HPA_SCALE_UP_PERIOD_SECONDS", 60),
        ("K8S_CADDY_HPA_SCALE_DOWN_STABILIZATION_WINDOW_SECONDS", 300),
        ("K8S_CADDY_HPA_SCALE_DOWN_PERCENT", 10),
        ("K8S_CADDY_HPA_SCALE_DOWN_PODS", 1),
        ("K8S_CADDY_HPA_SCALE_DOWN_PERIOD_SECONDS", 60),
        # VPA settings
        ("K8S_VPA_CONTROLLED_RESOURCES", ["cpu"]),
        ("K8S_VPA_UPDATE_MODE", "Off"),
        ("K8S_CMS_VPA_ENABLE", True),
        ("K8S_CMS_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_CMS_VPA_MAX_ALLOWED_CPU", "1000m"),
        ("K8S_CMS_VPA_MIN_ALLOWED_MEMORY", "1.5Gi"),
        ("K8S_CMS_VPA_MAX_ALLOWED_MEMORY", "4Gi"),
        ("K8S_CMS_WORKER_VPA_ENABLE", True),
        ("K8S_CMS_WORKER_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_CMS_WORKER_VPA_MAX_ALLOWED_CPU", "1000m"),
        ("K8S_CMS_WORKER_VPA_MIN_ALLOWED_MEMORY", "1.5Gi"),
        ("K8S_CMS_WORKER_VPA_MAX_ALLOWED_MEMORY", "4Gi"),
        ("K8S_LMS_VPA_ENABLE", True),
        ("K8S_LMS_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_LMS_VPA_MAX_ALLOWED_CPU", "1000m"),
        ("K8S_LMS_VPA_MIN_ALLOWED_MEMORY", "1.5Gi"),
        ("K8S_LMS_VPA_MAX_ALLOWED_MEMORY", "4Gi"),
        ("K8S_LMS_WORKER_VPA_ENABLE", True),
        ("K8S_LMS_WORKER_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_LMS_WORKER_VPA_MAX_ALLOWED_CPU", "1000m"),
        ("K8S_LMS_WORKER_VPA_MIN_ALLOWED_MEMORY", "1.5Gi"),
        ("K8S_LMS_WORKER_VPA_MAX_ALLOWED_MEMORY", "4Gi"),
        ("K8S_MFE_VPA_ENABLE", True),
        ("K8S_MFE_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_MFE_VPA_MAX_ALLOWED_CPU", "1000m"),
        ("K8S_MFE_VPA_MIN_ALLOWED_MEMORY", "30Mi"),
        ("K8S_MFE_VPA_MAX_ALLOWED_MEMORY", "100Mi"),
        ("K8S_CADDY_VPA_ENABLE", True),
        ("K8S_CADDY_VPA_MIN_ALLOWED_CPU", "10m"),
        ("K8S_CADDY_VPA_MAX_ALLOWED_CPU", "100m"),
        ("K8S_CADDY_VPA_MIN_ALLOWED_MEMORY", "50Mi"),
        ("K8S_CADDY_VPA_MAX_ALLOWED_MEMORY", "100Mi"),
        # CMS resources
        ("K8S_CMS_CPU_REQUEST", "20m"),
        ("K8S_CMS_MEMORY_REQUEST", "1.5Gi"),
        ("K8S_CMS_CPU_LIMIT", "100m"),
        ("K8S_CMS_MEMORY_LIMIT", "2Gi"),
        ("K8S_CMS_REPLICAS", 1),
        ("K8S_CMS_MAX_REPLICAS", 3),
        # CMS Worker resources
        ("K8S_CMS_WORKER_CPU_REQUEST", "20m"),
        ("K8S_CMS_WORKER_MEMORY_REQUEST", "1.5Gi"),
        ("K8S_CMS_WORKER_CPU_LIMIT", "100m"),
        ("K8S_CMS_WORKER_MEMORY_LIMIT", "2Gi"),
        ("K8S_CMS_WORKER_REPLICAS", 1),
        ("K8S_CMS_WORKER_MAX_REPLICAS", 3),
        # LMS resources
        ("K8S_LMS_CPU_REQUEST", "20m"),
        ("K8S_LMS_MEMORY_REQUEST", "1.5Gi"),
        ("K8S_LMS_CPU_LIMIT", "100m"),
        ("K8S_LMS_MEMORY_LIMIT", "2Gi"),
        ("K8S_LMS_REPLICAS", 1),
        ("K8S_LMS_MAX_REPLICAS", 3),
        # LMS Worker resources
        ("K8S_LMS_WORKER_CPU_REQUEST", "20m"),
        ("K8S_LMS_WORKER_MEMORY_REQUEST", "1.5Gi"),
        ("K8S_LMS_WORKER_CPU_LIMIT", "100m"),
        ("K8S_LMS_WORKER_MEMORY_LIMIT", "2Gi"),
        ("K8S_LMS_WORKER_REPLICAS", 1),
        ("K8S_LMS_WORKER_MAX_REPLICAS", 3),
        # MFE resources
        ("K8S_MFE_CPU_REQUEST", "10m"),
        ("K8S_MFE_MEMORY_REQUEST", "30Mi"),
        ("K8S_MFE_CPU_LIMIT", "100m"),
        ("K8S_MFE_MEMORY_LIMIT", "100Mi"),
        ("K8S_MFE_REPLICAS", 1),
        ("K8S_MFE_MAX_REPLICAS", 3),
        # Caddy resources
        ("K8S_CADDY_CPU_REQUEST", "10m"),
        ("K8S_CADDY_MEMORY_REQUEST", "50Mi"),
        ("K8S_CADDY_CPU_LIMIT", "100m"),
        ("K8S_CADDY_MEMORY_LIMIT", "100Mi"),
        ("K8S_CADDY_REPLICAS", 1),
        ("K8S_CADDY_MAX_REPLICAS", 3),
        # Pod disruption budgets
        ("K8S_CMS_PDB_ENABLE", True),
        ("K8S_CMS_WORKER_PDB_ENABLE", True),
        ("K8S_LMS_PDB_ENABLE", True),
        ("K8S_LMS_WORKER_PDB_ENABLE", True),
        ("K8S_MFE_PDB_ENABLE", True),
        ("K8S_CADDY_PDB_ENABLE", True),
        ("K8S_CADDY_MIN_AVAILABLE_REPLICAS", 1),
        ("K8S_LMS_MIN_AVAILABLE_REPLICAS", 1),
        ("K8S_LMS_WORKER_MIN_AVAILABLE_REPLICAS", 1),
        ("K8S_CMS_MIN_AVAILABLE_REPLICAS", 1),
        ("K8S_CMS_WORKER_MIN_AVAILABLE_REPLICAS", 1),
        ("K8S_MFE_MIN_AVAILABLE_REPLICAS", 1),
    ]
)

hooks.Filters.CONFIG_UNIQUE.add_items(
    [
        # Add settings that don't have a reasonable default for all users here.
        # For instance: passwords, secret keys, etc.
        # Each new setting is a pair: (setting_name, unique_generated_value).
        # Prefix your setting names with 'K8S_'.
        # For example:
        ### ("K8S_SECRET_KEY", "{{ 24|random_string }}"),
    ]
)

hooks.Filters.CONFIG_OVERRIDES.add_items(
    [
        # Danger zone!
        # Add values to override settings from Tutor core or other plugins here.
        # Each override is a pair: (setting_name, new_value). For example:
        ### ("PLATFORM_NAME", "My platform"),
    ]
)


########################################
# INITIALIZATION TASKS
########################################

# To add a custom initialization task, create a bash script template under:
# tutork8s/templates/k8s/tasks/
# and then add it to the MY_INIT_TASKS list. Each task is in the format:
# ("<service>", ("<path>", "<to>", "<script>", "<template>"))
MY_INIT_TASKS: list[tuple[str, tuple[str, ...]]] = [
    # For example, to add LMS initialization steps, you could add the script template at:
    # tutork8s/templates/k8s/tasks/lms/init.sh
    # And then add the line:
    ### ("lms", ("k8s", "tasks", "lms", "init.sh")),
]


# For each task added to MY_INIT_TASKS, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service, template_path in MY_INIT_TASKS:
    full_path: str = str(
        importlib_resources.files("tutork8s")
        / os.path.join("templates", *template_path)
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))


########################################
# DOCKER IMAGE MANAGEMENT
########################################


# Images to be built by `tutor images build`.
# Each item is a quadruple in the form:
#     ("<tutor_image_name>", ("path", "to", "build", "dir"), "<docker_image_tag>", "<build_args>")
hooks.Filters.IMAGES_BUILD.add_items(
    [
        # To build `myimage` with `tutor images build myimage`,
        # you would add a Dockerfile to templates/k8s/build/myimage,
        # and then write:
        ### (
        ###     "myimage",
        ###     ("plugins", "k8s", "build", "myimage"),
        ###     "docker.io/myimage:{{ K8S_VERSION }}",
        ###     (),
        ### ),
    ]
)


# Images to be pulled as part of `tutor images pull`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PULL.add_items(
    [
        # To pull `myimage` with `tutor images pull myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ K8S_VERSION }}",
        ### ),
    ]
)


# Images to be pushed as part of `tutor images push`.
# Each item is a pair in the form:
#     ("<tutor_image_name>", "<docker_image_tag>")
hooks.Filters.IMAGES_PUSH.add_items(
    [
        # To push `myimage` with `tutor images push myimage`, you would write:
        ### (
        ###     "myimage",
        ###     "docker.io/myimage:{{ K8S_VERSION }}",
        ### ),
    ]
)


########################################
# TEMPLATE RENDERING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

hooks.Filters.ENV_TEMPLATE_ROOTS.add_items(
    # Root paths for template files, relative to the project root.
    [
        str(importlib_resources.files("tutork8s") / "templates"),
    ]
)

hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    # For each pair (source_path, destination_path):
    # templates at ``source_path`` (relative to your ENV_TEMPLATE_ROOTS) will be
    # rendered to ``source_path/destination_path`` (relative to your Tutor environment).
    # For example, ``tutork8s/templates/k8s/build``
    # will be rendered to ``$(tutor config printroot)/env/plugins/k8s/build``.
    [
        ("k8s/build", "plugins"),
        ("k8s/apps", "plugins"),
    ],
)


########################################
# PATCH LOADING
# (It is safe & recommended to leave
#  this section as-is :)
########################################

# For each file in tutork8s/patches,
# apply a patch based on the file's name and contents.
for path in glob(str(importlib_resources.files("tutork8s") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))


########################################
# CUSTOM JOBS (a.k.a. "do-commands")
########################################

# A job is a set of tasks, each of which run inside a certain container.
# Jobs are invoked using the `do` command, for example: `tutor local do importdemocourse`.
# A few jobs are built in to Tutor, such as `init` and `createuser`.
# You can also add your own custom jobs:


# To add a custom job, define a Click command that returns a list of tasks,
# where each task is a pair in the form ("<service>", "<shell_command>").
# For example:
### @click.command()
### @click.option("-n", "--name", default="plugin developer")
### def say_hi(name: str) -> list[tuple[str, str]]:
###     """
###     An example job that just prints 'hello' from within both LMS and CMS.
###     """
###     return [
###         ("lms", f"echo 'Hello from LMS, {name}!'"),
###         ("cms", f"echo 'Hello from CMS, {name}!'"),
###     ]


# Then, add the command function to CLI_DO_COMMANDS:
## hooks.Filters.CLI_DO_COMMANDS.add_item(say_hi)

# Now, you can run your job like this:
#   $ tutor local do say-hi --name="Andrés González"


#######################################
# CUSTOM CLI COMMANDS
#######################################

# Your plugin can also add custom commands directly to the Tutor CLI.
# These commands are run directly on the user's host computer
# (unlike jobs, which are run in containers).

# To define a command group for your plugin, you would define a Click
# group and then add it to CLI_COMMANDS:


### @click.group()
### def k8s() -> None:
###     pass


### hooks.Filters.CLI_COMMANDS.add_item(k8s)


# Then, you would add subcommands directly to the Click group, for example:


### @k8s.command()
### def example_command() -> None:
###     """
###     This is helptext for an example command.
###     """
###     print("You've run an example command.")


# This would allow you to run:
#   $ tutor k8s example-command
