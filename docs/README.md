# Sphinx documentation


## Quick start 

### Static build


First install dependencies:

```
pipenv install --dev
```

Build the documentation locally:

```
pipenv run make html
```

This will create a subdirectory `/build/html`. To browse the documents created
open `/build/html/index.html` in a web browser.


### Auto-build

It is also possible to have the documentation be automatically rebuilt every
time a change is made using `sphinx-autobuild`. This can be started from the
`docs` directory with the command

```
pipenv run sphinx-autobuild src build/html
```

This will start a web server at the address <http://localhost:8000/> which
serves the current version of the documentation and is updated every time a
change is made to any of the documentation source files.
