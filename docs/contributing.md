# Contributing

Contributions are welcome and really appreciated.

## Issues

If you are unsure how to fix an issue you find, please log an issue in the 
project repository.

## Environment Setup

Estrade is dockerized, so the only requirements are Docker and Docker-Compose.

### Install

```
# clone repository
$ git clone git@github.com:cimourdain/estrade.git
$ make init
```

That's it.

## Developement

1. Start a new branch : `git checkout -b <branch_name>`
2. Edit code

### Before commiting

- Format your code with `make format`.
- Review documentation with `make docs-serve` (use `docker inspect` to find the ip where the doc is exposed locally.) 
- Apply pre-commits with `make pre-commit`

**Checks:**

- Check that the tests are passing : `make test`
- Check that the style is valid: `make style`
- Check that doc can be properly build: `make docs`
- Check that pre-commit updates were applied: `make pre-commit-check`

!!!note
    
    You can run call checks at once with `make ci`
    
!!!note
    
    If you are unsure about how to fix a failing check, don't worry, we'll be 
    happy to help you during the code review.

## Commit messages

Commit message must follow the [conventional commit specification](https://www.conventionalcommits.org/en/v1.0.0/#specification).

!!!note
    
    During developement you are highly incited to use fixups:
    ```
        $ git commit --fixup=<commit to fixup SHA>
    ```