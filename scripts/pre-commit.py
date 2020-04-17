import difflib
from typing import List, Dict

import click
import subprocess
from jinja2 import Template


COMMANDS = {
    "app_name": "poetry version | grep -Eo '^[^ ]+'",
    "version": "poetry version | grep -oE '[^ ]+$'",
    "git_branch": "echo ${BRANCH_NAME}",
    "coverage_pct": "poetry run pytest tests/ --cov=$(poetry version | grep -Eo '^[^ ]+') | grep TOTAL | grep -oE '[^ ]+$'",
    "complexity": "poetry run radon cc $(poetry version | grep -Eo '^[^ ]+')/ | grep 'Average complexity' | cut -d: -f2",
}


def get_command_stdout(command: List[str]) -> str:
    try:
        ps = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        response = ps.communicate()[0].decode('utf-8').replace("\n", "").strip()
    except:
        raise click.ClickException(f"😭 Error running command {command}")

    return response


def build_vars(required_variables: List[str]) -> Dict[str, str]:
    vars = {var: get_command_stdout(COMMANDS.get(var)) for var in
            required_variables}
    return vars


def files_diff(expected, actual):
    expected = expected.splitlines(1)
    actual = actual.splitlines(1)
    diff = difflib.unified_diff(
            expected,
            actual,
    )
    click.echo("".join(diff))


@click.group()
def cli():
    pass

@cli.command()
@click.option(
    '-c',
    '--check-only',
    default=False,
    help='Check only.'
)
def render_readme(check_only):
    required_variables = ["app_name", "version", "git_branch", "coverage_pct", "complexity"]
    vars = build_vars(required_variables)

    vars["readthedocs_version"] = "latest" if vars["git_branch"] == "master" else vars["git_branch"]
    vars["include_badges"] = True
    vars["include_doc_link"] = True
    readme_rendered = Template(open("README.template").read()).render(**vars)

    vars["include_doc_link"] = False
    readme_docs_rendered = Template(open("README.template").read()).render(**vars)

    if check_only:
        readme_current_content = open("README.md", "r").read()
        if readme_current_content != readme_rendered:
            files_diff(
                readme_rendered,
                readme_current_content,
            )
            raise click.ClickException("🥶 README.md was not generated from template.")
        readme_docs_current = open("docs/index.md", "r").read()
        if readme_docs_current != readme_docs_rendered:
            files_diff(
                readme_docs_rendered,
                readme_docs_current,
            )
            raise click.ClickException("🥶 docs/index.md was not generated from template.")
        click.echo("🥳 README is valid")
        return True

    with open("README.md", "w+") as readme:
        readme.write(readme_rendered)

    with open("docs/index.md", "w+") as readme:
        readme.write(readme_docs_rendered)

    click.echo("😎 README is updated")

@cli.command()
@click.option(
    '-c',
    '--check-only',
    default=False,
    help='Check only.'
)
def docs_requirements(check_only):
    cmd = "poetry export -f requirements.txt --without-hashes --dev | grep -E -- 'mkdocs|pygments'"

    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    expected_requirements = ps.communicate()[0].decode('utf-8')
    if check_only:
        current_requirements_content = open("docs/requirements.txt", "r").read()
        if current_requirements_content != expected_requirements:
            files_diff(
                expected_requirements,
                current_requirements_content,
            )
            raise click.ClickException("🥶 docs requirements not up to date.")
        click.echo("🥳 docs requirements is up to date")
        return True

    with open("docs/requirements.txt", "w+") as readme:
        readme.write(expected_requirements)

    click.echo("😎 docs requirements is updated")


if __name__ == '__main__':
    cli()

