"""Cookiecutter post_gen_project hook.

See: https://cookiecutter.readthedocs.io/en/1.7.2/advanced/hooks.html
"""

import os
import sys
import json
import urllib
import shutil
import fileinput
import subprocess
from configparser import ConfigParser
from urllib import request
from urllib.request import Request
from datetime import date
from pathlib import Path


COOKIECUTTER_SETTINGS = {
    "full_name": "{{ cookiecutter.full_name }}",
    "email": "{{ cookiecutter.email }}",
    "github_username": "{{ cookiecutter.github_username }}",
    "project_name": "{{ cookiecutter.project_name }}",
    "project_slug": "{{ cookiecutter.project_slug }}",
    "project_summary": "{{ cookiecutter.project_summary }}",
    "project_license": "{{ cookiecutter.project_license }}",
    "project_code_of_conduct": "{{ cookiecutter.project_code_of_conduct }}",
    "project_python_poetry": "{{ cookiecutter.project_python_poetry }}",
}

LICENSES = {
    "mit": "MIT",
    "apache20": "Apache-2.0",
    "no_license": "No License",
}

CODES_OF_CONDUCT = {
    "contributor_covenant": "Contributor Covenant",
    "citizen": "Citizen Code Of Conduct",
    "no_code_of_conduct": "No Code of Conduct",
}


def github_api(resource_path, headers=None):
    """Simple/limited wrapper around GitHub API."""
    base_url = "https://api.github.com"
    resource_url = f"{base_url}/{resource_path}"

    try:
        req = Request(resource_url, headers=headers)
        res = request.urlopen(req)
        data = json.loads(res.read())
    except Exception as e:
        print(f"Request to {resource_url} failed: {e}")
        sys.exit(1)

    return data


def get_license():
    """Get the selected license from GitHub API."""
    full_name = COOKIECUTTER_SETTINGS["full_name"]
    email = COOKIECUTTER_SETTINGS["email"]
    project_license = COOKIECUTTER_SETTINGS["project_license"]
    license_name = project_license.lower().replace(" ", "_")
    resource_path = f"licenses/{license_name}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    if project_license == LICENSES["no_license"]:
        return

    data = github_api(resource_path, headers=headers)
    content = data.get("body", "")

    if project_license == LICENSES["mit"]:
        write_license_mit(content, full_name, email)
    elif project_license == LICENSES["apache20"]:
        write_license_apache2(content, full_name, email)
    else:
        write_license(content)


def write_license(content):
    """Write content to a LICENSE file."""
    with open("LICENSE", "w") as f:
        print("Creating the LICENSE file...")
        f.write(content)


def write_license_mit(content, full_name, email):
    """Write an MIT LICENSE."""
    year = date.today().year
    content = content.replace("[year]", str(year)).replace(
        "[fullname]", f"{full_name} <{email}>"
    )
    write_license(content)


def write_license_apache2(content, full_name, email):
    """Write an Apache 2.0 LICENSE."""
    year = date.today().year
    content = content.replace("[yyyy]", str(year)).replace(
        "[name of copyright owner]", f"{full_name} <{email}>"
    )
    write_license(content)


def get_code_of_conduct():
    """Get the selected code of conduct from GitHub API."""
    email = COOKIECUTTER_SETTINGS["email"]
    project_code_of_conduct = COOKIECUTTER_SETTINGS["project_code_of_conduct"]
    code_of_conduct_name = project_code_of_conduct.lower().replace(" ", "_")
    resource_path = f"codes_of_conduct/{code_of_conduct_name}"
    headers = {"Accept": "application/vnd.github.scarlet-witch-preview+json"}

    if project_code_of_conduct == CODES_OF_CONDUCT["no_code_of_conduct"]:
        return

    data = github_api(resource_path, headers=headers)
    content = data.get("body", "")

    if project_code_of_conduct == CODES_OF_CONDUCT["contributor_covenant"]:
        write_code_of_conduct_contributor_covenant(content, email)
    elif project_code_of_conduct == CODES_OF_CONDUCT["citizen"]:
        write_code_of_conduct_citizen(content)
    else:
        write_code_of_conduct(content)


def write_code_of_conduct(content):
    """Write content to a CODE_OF_CONDUCT.md."""
    with open("CODE_OF_CONDUCT.md", "w") as f:
        print("Creating the CODE_OF_CONDUCT.md file...")
        f.write(content)


def write_code_of_conduct_contributor_covenant(content, email):
    """Write a Contributor Covenant code of conduct."""
    content = content.replace("[INSERT_EMAIL_ADDRESS]", email)
    write_code_of_conduct(content)


def write_code_of_conduct_citizen(content):
    """Write a Citizen Code of Conduct."""
    write_code_of_conduct(content)
    print("> Remember to update the many replacements in this code of conduct!!!")


def remove_donotrender_ext():
    """Remove .donotrenderext from all files.

    This template uses a custom `.donotrender` extension
    which is set as part of the _copy_without_render config
    in [cookiecutter.json](./cookiecutter.json).

    This convention was created to keep config simple
    and create a more declarative approach for telling
    cookiecutter to ignore files.

    This function removes that extension to restore
    the original filename/extension.
    """
    ext = "donotrender"
    paths = Path.cwd().rglob(f"*.{ext}")

    print("Removing .donotrender extensions...")

    for p in paths:
        p.replace(p.with_suffix(""))


def poetry_init():
    """Initialize poetry."""
    print("Creating pyproject.toml...")

    if not shutil.which("poetry") is not None:
        print("poetry is not installed, but required! Skipping poetry init...")
        return

    name = COOKIECUTTER_SETTINGS["project_slug"]
    description = COOKIECUTTER_SETTINGS["project_summary"]
    author = COOKIECUTTER_SETTINGS["full_name"]
    license = COOKIECUTTER_SETTINGS["project_license"]
    python = COOKIECUTTER_SETTINGS["project_python_poetry"]
    project_slug = COOKIECUTTER_SETTINGS["project_slug"]
    github_username = COOKIECUTTER_SETTINGS["github_username"]

    # NOTE: Installs default dev dependencies only.
    cmd = [
        *("poetry", "init", "--no-interaction", "--quiet"),
        *("--name", name),
        *("--description", description),
        *("--author", author),
        *("--license", license),
        *("--python", python),
        *("--dev-dependency", "black"),
        *("--dev-dependency", "pydocstyle"),
        *("--dev-dependency", "pdoc3"),
        *("--dev-dependency", "pytest"),
        *("--dev-dependency", "coverage"),
        *("--dev-dependency", "pdbpp"),
        *("--dev-dependency", "click"),
        *("--dev-dependency", "klak"),
    ]
    subprocess.run(cmd, check=True)

    # NOTE: Set additional poetry config not available from `poetry init`
    pyproject_path = Path("./pyproject.toml")
    config = ConfigParser()
    config.read(pyproject_path)
    config_poetry = config["tool.poetry"]
    settings = {
        "readme": '"README.md"',
        "keywords": "[]",
        "classifiers": "[]",
    }
    if github_username:
        settings["repository"] = f'"https://github.com/{github_username}"'
        settings[
            "documentation"
        ] = f'"https://{github_username}.github.io/{project_slug}/"'

    for k, v in settings.items():
        config_poetry[k] = v

    with open(str(pyproject_path), "w") as f:
        config.write(f)


def run():
    """Run post gen hook functions."""
    remove_donotrender_ext()
    get_license()
    get_code_of_conduct()
    poetry_init()


# NOTE: Do not delete this or the hook will not run.
run()
