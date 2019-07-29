# Developer notes


## Publishing code artifacts (using git tags)

The CI script is configured to publish artifacts (Docker images & Python
packages) when it a new tag is created patterns described in the sections below:

### Tagging Docker images

**Tag pattern**: `<image name>==<tag>`

Examples:

```bash
git tag -a pytango-9.3.0==alpine3.10 -m "<message>"
git push --tags

git tag -a tangods-sdp-subarray==0.3.0 -m "<message>"
git push --tags
```

### Tagging Python packages

**Tag pattern**: `<Package name>==<Package version>`

Example:

```bash
git tag -a ska-sdp-subarray==0.3.2 -m "<message>"
git push --tags
```

### Working with git tags

#### List tags

To list local tags:

```bash
git tag
```

To list remote tags:

```bash
git ls-remote --tags origin
```

#### Removing a tag

To remove a local tag:

```bash
git tag -d <tag id>
```

To remove a remote tag:

```bash
git push origin --delete <tag id>
```

*(This can also be achieved though the repository web-ui)*
